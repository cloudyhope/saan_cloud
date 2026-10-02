"""Spare-part requests raised from a visit; a warehouse manager fulfils them as a stock transfer to the worker."""
import uuid

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import DeleteCreateUpdateGetPermission
from warehouse.models import PartRequest, Ware, WarehouseLocation, WarehouseTransactionLine, WareVisitType
from warehouse.stock import create_stock_transfer
from warehouse.views import require_warehouse_manager, warehouse_project_id

OPEN_VISIT = ('0', '1', '5', '6')


def person(user):
    return ' '.join(filter(None, (user.first_name, user.last_name))) or 'کاربر' if user else ''


def ware_label(ware):
    return ware.name_fa or ware.name_en or f'کالا {ware.pk}'


def part_request_row(row):
    unit = row.ware.unit
    return {
        'id': row.pk, 'visit': row.visit_id, 'ware': row.ware_id, 'ware_name': ware_label(row.ware),
        'identifier': row.ware.identifier or '', 'unit': (unit.unit_fa or unit.unit_abbreviation or '') if unit else '',
        'amount': row.amount, 'note': row.note, 'status': row.status, 'status_label': row.get_status_display(),
        'requester': person(row.requester), 'location': row.location.name_fa if row.location else '',
        'decision_note': row.decision_note, 'decided_by': person(row.decided_by),
        'created_at': row.created_at, 'decided_at': row.decided_at, 'transaction': row.stock_transaction_id,
    }


def location_stock(ware_ids, project_id):
    """{ware_id: [{location, name, amount}]} for warehouses of the project with positive stock."""
    rows = (WarehouseTransactionLine.objects.filter(ware_id__in=ware_ids, user__isnull=True,
                                                    location__projects__id=project_id)
            .values('ware_id', 'location_id', 'location__name_fa').annotate(amount=Sum('amount')))
    stock = {}
    for row in rows:
        if row['amount'] and row['amount'] > 0:
            stock.setdefault(row['ware_id'], []).append(
                {'location': row['location_id'], 'name': row['location__name_fa'] or 'انبار', 'amount': row['amount']})
    return stock


class PartRequestInput(serializers.Serializer):
    ware = serializers.IntegerField(min_value=1)
    amount = serializers.IntegerField(min_value=1, max_value=1000)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default='')


class PromoterPartRequestView(APIView):
    """The assigned worker lists and raises part requests for an open visit."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def visit(self, request, id, editable=False):
        from visit.views import assigned_field_visit
        visit = assigned_field_visit(request, id, editable=editable, view=self)
        if request.user.id not in (visit.expert_id, visit.promoter_id):
            raise NotFound()
        return visit

    def payload(self, request, visit):
        project_id = visit.type.project_id
        suggested = set(WareVisitType.objects.filter(visit_type=visit.type).values_list('ware_id', flat=True))
        wares = list(Ware.objects.filter(project_id=project_id, is_active=True)
                     .select_related('unit').order_by('-priority', 'name_fa', 'id')[:300])
        stock = location_stock([ware.pk for ware in wares], project_id)
        mine = dict(WarehouseTransactionLine.objects.filter(user=request.user, ware__in=wares)
                    .values_list('ware_id').annotate(total=Sum('amount')))
        return {
            'open': visit.status in OPEN_VISIT,
            'requests': [part_request_row(row) for row in visit.part_requests.filter(requester=request.user)
                         .select_related('ware__unit', 'requester', 'location', 'decided_by')],
            'wares': sorted([{'id': ware.pk, 'name': ware_label(ware), 'identifier': ware.identifier or '',
                              'unit': (ware.unit.unit_fa or '') if ware.unit else '', 'suggested': ware.pk in suggested,
                              'in_stock': sum(item['amount'] for item in stock.get(ware.pk, [])),
                              'mine': mine.get(ware.pk) or 0} for ware in wares],
                            key=lambda item: not item['suggested']),
        }

    def get(self, request, id):
        return Response(self.payload(request, self.visit(request, id)))

    def post(self, request, id):
        visit = self.visit(request, id, editable=True)
        data = PartRequestInput(data=request.data)
        data.is_valid(raise_exception=True)
        ware = Ware.objects.filter(pk=data.validated_data['ware'], project_id=visit.type.project_id,
                                   is_active=True).first()
        if ware is None:
            raise ValidationError({'ware': 'کالا در این پروژه فعال نیست.'})
        if visit.part_requests.filter(requester=request.user, ware=ware, status=PartRequest.PENDING).exists():
            raise ValidationError({'ware': 'برای این قطعه درخواست در انتظار دارید.'})
        with transaction.atomic():
            row = PartRequest.objects.create(project_id=visit.type.project_id, visit=visit, requester=request.user,
                                             ware=ware, amount=data.validated_data['amount'],
                                             note=data.validated_data['note'].strip())
            from notification.in_app import notify_part_request
            transaction.on_commit(lambda: notify_part_request(row))
        return Response(self.payload(request, visit), status=201)


class PromoterPartRequestCancelView(APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, id):
        project_id = warehouse_project_id(request)
        with transaction.atomic():
            row = PartRequest.objects.select_for_update().filter(
                pk=id, project_id=project_id, requester=request.user).first()
            if row is None:
                raise NotFound()
            if row.status != PartRequest.PENDING:
                raise ValidationError({'status': 'فقط درخواست در انتظار قابل لغو است.'})
            row.status, row.decided_at = PartRequest.CANCELED, timezone.now()
            row.save(update_fields=['status', 'decided_at'])
        return Response(part_request_row(row))


class PartRequestListView(APIView):
    """Warehouse queue of part requests with per-warehouse stock to pick the source."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request):
        require_warehouse_manager(request, self)
        project_id = warehouse_project_id(request)
        rows = PartRequest.objects.filter(project_id=project_id).select_related(
            'ware__unit', 'requester', 'location', 'decided_by', 'visit__building')
        status = request.query_params.get('status') or ''
        if status:
            if status not in dict(PartRequest.STATUS_CHOICES):
                raise ValidationError({'status': 'وضعیت نامعتبر است.'})
            rows = rows.filter(status=status)
        search = (request.query_params.get('search') or '').strip()
        if search:
            rows = rows.filter(Q(ware__name_fa__icontains=search) | Q(ware__identifier__icontains=search)
                               | Q(requester__first_name__icontains=search) | Q(requester__last_name__icontains=search)
                               | Q(visit__building__verbose_name__icontains=search))
        try:
            limit = min(max(int(request.query_params.get('limit', 50)), 1), 200)
            offset = max(int(request.query_params.get('offset', 0)), 0)
        except ValueError:
            raise ValidationError({'pagination': 'صفحه‌بندی نامعتبر است.'})
        page = list(rows[offset:offset + limit])
        stock = location_stock({row.ware_id for row in page if row.status == PartRequest.PENDING}, project_id)
        results = []
        for row in page:
            item = part_request_row(row)
            building = row.visit.building
            item['building'] = (building.verbose_name or building.name or building.code) if building else ''
            item['stock'] = stock.get(row.ware_id, []) if row.status == PartRequest.PENDING else []
            results.append(item)
        counts = dict(PartRequest.objects.filter(project_id=project_id).values_list('status').annotate(n=Count('id')))
        return Response({'count': rows.count(), 'results': results, 'pending': counts.get(PartRequest.PENDING, 0)})


class PartRequestDecisionInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=('fulfill', 'reject'))
    location = serializers.IntegerField(min_value=1, required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default='')


class PartRequestDecisionView(APIView):
    """Fulfil (transfer from a chosen warehouse to the requester) or reject a pending request."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, id):
        require_warehouse_manager(request, self)
        project_id = warehouse_project_id(request)
        data = PartRequestDecisionInput(data=request.data)
        data.is_valid(raise_exception=True)
        action, note = data.validated_data['action'], data.validated_data['note'].strip()
        if action == 'reject' and len(note) < 5:
            raise ValidationError({'note': 'دلیل رد درخواست را بنویسید.'})
        with transaction.atomic():
            row = get_object_or_404(PartRequest.objects.select_for_update(), pk=id, project_id=project_id)
            if row.status != PartRequest.PENDING:
                raise ValidationError({'status': 'این درخواست قبلاً بررسی شده است.'})
            if action == 'fulfill':
                location = WarehouseLocation.objects.filter(pk=data.validated_data.get('location'),
                                                            projects__id=project_id).first()
                if location is None:
                    raise ValidationError({'location': 'انبار مبدأ را انتخاب کنید.'})
                values = {
                    'lines': [
                        {'ware': row.ware_id, 'amount': -row.amount, 'side': 'FROM', 'involved': 'LOCATION',
                         'location': location.pk, 'user': None},
                        {'ware': row.ware_id, 'amount': row.amount, 'side': 'TO', 'involved': 'USER',
                         'location': None, 'user': row.requester_id},
                    ],
                    'description': f'تحویل درخواست قطعه {row.pk} برای مأموریت {row.visit_id}'
                                   + (f' — {note}' if note else ''),
                    'request_key': uuid.uuid5(uuid.NAMESPACE_URL, f'saan:part-request:{row.pk}'),
                    'kind': 'TRANSFER',
                }
                entry, _ = create_stock_transfer(request, self, values)
                row.location, row.stock_transaction = location, entry
                row.status = PartRequest.FULFILLED
            else:
                row.status = PartRequest.REJECTED
            row.decision_note, row.decided_by, row.decided_at = note, request.user, timezone.now()
            row.save()
            from notification.in_app import notify_part_decision
            transaction.on_commit(lambda: notify_part_decision(row))
        return Response(part_request_row(row))
