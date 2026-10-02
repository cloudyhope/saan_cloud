"""Management dashboard: one scoped snapshot of field work and service operations for a period.

The admin dashboard filters and cross-filters on the client, so the API returns compact visit rows
for the period (plus the open backlog) and small aggregates for the other service areas.
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Avg, Count, OuterRef, Q, Subquery, Sum
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import DeleteCreateUpdateGetPermission
from visit.asset_access import AssetAccess
from visit.management import current_management_q
from visit.priority import annotate_visits
from visit.models import (BuildingClient, ClientVisitFeedback, RepairCase, Ticket, Visit, VisitReportSnapshot,
                          WarrantyClaim)

LOCAL = ZoneInfo('Asia/Tehran')
OPEN = (Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND)
MAX_DAYS = 366
MAX_ROWS = 5000


def _day(value, name):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError({name: 'تاریخ باید به شکل YYYY-MM-DD باشد.'})


def _start(day):
    return datetime.combine(day, time.min, tzinfo=LOCAL)


def _local(value):
    return value.astimezone(LOCAL).isoformat(timespec='minutes') if value else None


def _name(user_row):
    first, last, username, full = user_row
    return full or ' '.join(part for part in (first, last) if part) or username


class AdminDashboardView(APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request):
        access = AssetAccess(request, self)
        if not access.project_wide:
            raise PermissionDenied('داشبورد مدیریتی نیازمند دسترسی کل پروژه است.')
        project_id = access.project_id
        today = datetime.now(LOCAL).date()
        end = _day(request.query_params.get('to'), 'to') if request.query_params.get('to') else today
        begin = _day(request.query_params.get('from'), 'from') if request.query_params.get('from') else end - timedelta(days=29)
        if begin > end:
            raise ValidationError({'from': 'ابتدای بازه باید پیش از انتهای آن باشد.'})
        if (end - begin).days >= MAX_DAYS:
            raise ValidationError({'from': 'بازه حداکثر یک سال است.'})
        window_start, window_end = _start(begin), _start(end + timedelta(days=1))
        length = end - begin + timedelta(days=1)
        previous_start, previous_end = _start(begin - length), window_start

        visits = access.visits  # project-wide: every live visit of the project
        completed_at = VisitReportSnapshot.objects.filter(visit=OuterRef('pk')).order_by('created_at').values('created_at')[:1]
        rating = ClientVisitFeedback.objects.filter(visit=OuterRef('pk'), rating__isnull=False).values('visit').annotate(
            value=Avg('rating')).values('value')
        rows = annotate_visits(visits).annotate(completed_at=Subquery(completed_at), client_rating=Subquery(rating)).filter(
            Q(datetime_created__gte=window_start, datetime_created__lt=window_end)
            | Q(status__in=OPEN, is_active=True)
            | Q(due_date__gte=begin, due_date__lte=end)
            | Q(completed_at__gte=window_start, completed_at__lt=window_end)
        ).order_by('-datetime_created', '-id').values(
            'id', 'status', 'is_active', 'type_id', 'expert_id', 'promoter_id', 'building_id', 'datetime_created',
            'start_datetime', 'has_due_date', 'due_date', 'completed_at', 'client_rating', 'priority_value')
        rows = list(rows[:MAX_ROWS + 1])
        truncated = len(rows) > MAX_ROWS
        rows = rows[:MAX_ROWS]
        ids = [row['id'] for row in rows]
        pending = set(Visit.service_submissions.through.objects.filter(visit_id__in=ids).values_list('visit_id', flat=True))
        building_ids = {row['building_id'] for row in rows if row['building_id']}
        managers = dict(BuildingClient.objects.filter(building_id__in=building_ids, client__project_id=project_id)
                        .filter(current_management_q()).order_by('start_at').values_list('building_id', 'client_id'))

        out, experts, types = [], set(), set()
        for row in rows:
            worker = row['expert_id'] or row['promoter_id']
            completed = row['completed_at']
            if completed is None and row['status'] in (Visit.COMPLETED, Visit.APPROVED, Visit.REJECTED):
                # Legacy reports have no frozen snapshot; their last change may be a bulk import, so the
                # field start is the closest trustworthy completion date.
                completed = row['start_datetime']
            out.append({
                'id': row['id'], 's': row['status'], 'a': row['is_active'],
                'p': row['id'] in pending and not row['is_active'] and row['status'] == Visit.NOTVISITED,
                't': row['type_id'], 'e': worker, 'b': row['building_id'], 'c': managers.get(row['building_id']),
                'cr': _local(row['datetime_created']), 'st': _local(row['start_datetime']),
                'du': row['due_date'].isoformat() if row['has_due_date'] and row['due_date'] else None,
                'co': _local(completed), 'ra': round(row['client_rating'], 1) if row['client_rating'] else None,
                'pr': None if row['priority_value'] is None else round(row['priority_value'], 1),
            })
            if worker:
                experts.add(worker)
            types.add(row['type_id'])

        from django.contrib.auth.models import User
        from visit.models import Building, Client, VisitType
        lookups = {
            'experts': {pk: _name((first, last, username, full)) for pk, first, last, username, full in
                        User.objects.filter(pk__in=experts).values_list('pk', 'first_name', 'last_name', 'username',
                                                                         'extendeduser__full_name')},
            'types': dict((pk, verbose or title) for pk, verbose, title in
                          VisitType.objects.filter(pk__in=types).values_list('pk', 'verbose_name', 'title')),
            'buildings': dict((pk, verbose or name or code) for pk, verbose, name, code in
                              Building.objects.filter(pk__in=building_ids).values_list('pk', 'verbose_name', 'name', 'code')),
            'clients': dict((pk, name_fa or name) for pk, name_fa, name in
                            Client.objects.filter(pk__in=set(managers.values())).values_list('pk', 'name_fa', 'name')),
        }
        previous = visits.annotate(completed_at=Subquery(completed_at))
        repair_counts = dict(RepairCase.objects.filter(project_id=project_id).exclude(status__in=('DELIVERED', 'CANCELED'))
                             .values('status').annotate(total=Count('id')).values_list('status', 'total'))
        tickets = Ticket.objects.filter(project_id=project_id, is_deleted=False)
        from warehouse.models import Ware
        stock = Ware.objects.filter(project_id=project_id, is_active=True, is_for_use=True).annotate(
            total=Sum('warehousetransactionline__amount'))
        return Response({
            'range': {'from': begin.isoformat(), 'to': end.isoformat(), 'today': today.isoformat()},
            'visits': out, 'truncated': truncated, 'lookups': lookups,
            'previous': {
                'created': previous.filter(datetime_created__gte=previous_start, datetime_created__lt=previous_end).count(),
                'completed': previous.filter(completed_at__gte=previous_start, completed_at__lt=previous_end).count(),
            },
            'services': {
                'tickets': {'waiting': tickets.filter(status=Ticket.WAITING).count(),
                            'answered': tickets.filter(status=Ticket.ANSWERED).count(),
                            'created': tickets.filter(datetime_created__gte=window_start, datetime_created__lt=window_end).count()},
                'claims_pending': WarrantyClaim.objects.filter(project_id=project_id, status=WarrantyClaim.PENDING).count(),
                'repairs': repair_counts,
                'out_of_stock': sum(1 for ware in stock if (ware.total or 0) <= 0),
            },
        })
