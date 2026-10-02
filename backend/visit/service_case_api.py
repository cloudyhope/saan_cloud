"""Warranty decisions and auditable board-repair progression."""
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from auth_app.permissions import DeleteCreateUpdateGetPermission
from notification.in_app import notify_repair_event, notify_warranty_decision
from visit.models import (Client, Product, ProductElevator, RepairCase, RepairEvent, WarrantyClaim,
                          WarrantyContract)
from visit.service_case_access import ServiceCaseAccess
from warehouse.models import Ware, WarehouseTransactionLine
from warehouse.stock import create_stock_transfer


class WarrantyContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarrantyContract
        fields = ('id', 'project', 'client', 'product', 'reference', 'coverage_start',
                  'coverage_end', 'terms', 'exclusions', 'is_active', 'created_at')
        read_only_fields = ('id', 'project', 'created_at')


class WarrantyContractListCreateView(generics.ListCreateAPIView):
    serializer_class = WarrantyContractSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return ServiceCaseAccess(self.request, self).contracts.order_by('-id')

    def perform_create(self, serializer):
        access = ServiceCaseAccess(self.request, self)
        access.require_manager()
        values = serializer.validated_data
        access.validate_client_product(values['client'], values['product'], require_link=True)
        if values['coverage_end'] < values['coverage_start']:
            raise ValidationError({'coverage_end': 'پایان پوشش نمی‌تواند پیش از شروع باشد.'})
        if WarrantyContract.objects.filter(project_id=access.project_id,
                                            reference=values['reference']).exists():
            raise ValidationError({'reference': 'شماره قرارداد در این پروژه تکراری است.'})
        serializer.save(project_id=access.project_id, created_by=self.request.user)


class WarrantyEligibleProductsView(generics.GenericAPIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        try:
            client_id = int(request.query_params.get('client'))
        except (TypeError, ValueError):
            raise ValidationError({'client': 'مشتری معتبر را انتخاب کنید.'})
        client = Client.objects.filter(pk=client_id, project_id=access.project_id).first()
        if client is None:
            raise NotFound()
        return Response([{'id': row.id, 'serial_number': row.serial_number or ''}
                         for row in access.linked_products(client).order_by('id')])


class WarrantyClaimSerializer(serializers.ModelSerializer):
    issue = serializers.CharField(max_length=2000, trim_whitespace=True)
    class Meta:
        model = WarrantyClaim
        fields = ('id', 'project', 'client', 'product', 'contract', 'visit', 'issue',
                  'status', 'decision_reason', 'opened_at', 'decided_at')
        read_only_fields = ('id', 'project', 'status', 'decision_reason', 'opened_at', 'decided_at')


class WarrantyClaimListCreateView(generics.ListCreateAPIView):
    serializer_class = WarrantyClaimSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return ServiceCaseAccess(self.request, self).claims.order_by('-opened_at', '-id')

    def perform_create(self, serializer):
        access = ServiceCaseAccess(self.request, self)
        values = serializer.validated_data
        client, product = values['client'], values['product']
        if not access.assets.project_wide and 'client' not in access.assets.scopes:
            access.require_manager()
        access.validate_client_product(client, product,
                                       client_write=not access.assets.project_wide,
                                       require_link=True)
        contract = values.get('contract')
        if contract is not None and (contract.project_id != access.project_id
                                     or contract.client_id != client.pk
                                     or contract.product_id != product.pk):
            raise ValidationError({'contract': 'قرارداد به همین کلاینت و قطعه تعلق ندارد.'})
        if contract is None:
            today = timezone.localdate()
            active_contracts = list(WarrantyContract.objects.filter(
                project_id=access.project_id, client=client, product=product,
                is_active=True, coverage_start__lte=today, coverage_end__gte=today,
            ).order_by('-coverage_start', '-id')[:2])
            if len(active_contracts) > 1:
                raise ValidationError({'contract': 'برای این قطعه چند قرارداد فعال وجود دارد؛ قرارداد را انتخاب کنید.'})
            contract = active_contracts[0] if active_contracts else None
        visit = values.get('visit')
        if visit is not None:
            if not access.assets.visits.filter(pk=visit.pk).exists():
                raise ValidationError({'visit': 'بازدید در محدوده دسترسی نیست.'})
            if not ProductElevator.objects.filter(
                product=product, elevator__buildingelevator__building_id=visit.building_id,
            ).exists():
                raise ValidationError({'visit': 'بازدید به محل نصب این قطعه مربوط نیست.'})
        serializer.save(project_id=access.project_id, opened_by=self.request.user,
                        status=WarrantyClaim.PENDING, contract=contract)


class WarrantyClaimDecisionInput(serializers.Serializer):
    status = serializers.ChoiceField(choices=(WarrantyClaim.COVERED, WarrantyClaim.DENIED))
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True, max_length=2000)


class WarrantyClaimDecisionView(generics.GenericAPIView):
    serializer_class = WarrantyClaimDecisionInput
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, id):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        with transaction.atomic():
            claim = access.claims.select_for_update().filter(pk=id).first()
            if claim is None:
                raise NotFound()
            if claim.status != WarrantyClaim.PENDING:
                raise ValidationError({'status': 'برای این ادعا قبلاً تصمیم ثبت شده است.'})
            claim.status = payload.validated_data['status']
            claim.decision_reason = payload.validated_data['reason']
            claim.decided_by = request.user
            claim.decided_at = timezone.now()
            claim.save(update_fields=['status', 'decision_reason', 'decided_by', 'decided_at'])
            notify_warranty_decision(claim)
        return Response(WarrantyClaimSerializer(claim).data)


class RepairEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairEvent
        fields = ('id', 'from_status', 'to_status', 'note', 'loaner_product',
                  'loaner_due_at', 'actor', 'at')


class RepairCaseSerializer(serializers.ModelSerializer):
    events = RepairEventSerializer(many=True, read_only=True)
    materials = serializers.SerializerMethodField()

    def get_materials(self, obj):
        lines = WarehouseTransactionLine.objects.filter(
            transaction__repair_case=obj, amount__lt=0,
        ).select_related('ware', 'type', 'transaction').order_by('transaction__datetime_created', 'id')
        return [{'transaction_id': line.transaction_id, 'ware': line.ware_id,
                 'ware_name': line.ware.name_fa or line.ware.name_en or str(line.ware_id),
                 'quantity': -line.amount,
                 'at': line.transaction.datetime_created,
                 'description': line.transaction.description} for line in lines]

    class Meta:
        model = RepairCase
        fields = ('id', 'rma_key', 'project', 'client', 'product', 'claim', 'serial_snapshot',
                  'status', 'received_at', 'delivered_at', 'diagnosis', 'work_performed',
                  'test_result', 'loaner_product', 'loaner_due_at', 'loaner_returned_at', 'events', 'materials')
        read_only_fields = ('id', 'rma_key', 'project', 'serial_snapshot', 'status', 'received_at',
                            'delivered_at', 'diagnosis', 'work_performed', 'test_result',
                            'loaner_product', 'loaner_due_at', 'loaner_returned_at', 'events', 'materials')


class RepairCaseListCreateView(generics.ListCreateAPIView):
    serializer_class = RepairCaseSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return ServiceCaseAccess(self.request, self).repairs.prefetch_related('events').order_by('-id')

    def perform_create(self, serializer):
        access = ServiceCaseAccess(self.request, self)
        access.require_manager()
        values = serializer.validated_data
        client, product = values['client'], values['product']
        claim = values.get('claim')
        access.validate_client_product(client, product, require_link=claim is None)
        if claim is not None and (claim.project_id != access.project_id
                                  or claim.client_id != client.pk or claim.product_id != product.pk):
            raise ValidationError({'claim': 'ادعا به همین کلاینت و قطعه تعلق ندارد.'})
        with transaction.atomic():
            repair = serializer.save(project_id=access.project_id, created_by=self.request.user,
                                     serial_snapshot=product.serial_number or '')
            event = RepairEvent.objects.create(case=repair, to_status=RepairCase.RECEIVED,
                                               actor=self.request.user, note='دریافت قطعه ثبت شد.')
            notify_repair_event(repair, event)


class RepairCaseDetailView(generics.RetrieveAPIView):
    serializer_class = RepairCaseSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]
    lookup_field = 'id'

    def get_queryset(self):
        return ServiceCaseAccess(self.request, self).repairs.prefetch_related('events')


class RepairMaterialInput(serializers.Serializer):
    ware = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    source_type = serializers.ChoiceField(choices=('LOCATION', 'USER'))
    source_id = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()


class RepairCaseMaterialView(generics.GenericAPIView):
    serializer_class = RepairMaterialInput
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request, id):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        if not access.repairs.filter(pk=id).exists():
            raise NotFound()
        parties = WarehouseTransactionLine.objects.filter(
            ware__project_id=access.project_id, ware__is_active=True,
        ).values('ware_id', 'ware__name_fa', 'ware__name_en', 'location_id',
                 'location__name_fa', 'user_id', 'user__username').annotate(
                     available=Sum('amount')).filter(available__gt=0)
        options = []
        for row in parties:
            party = {'location_id': row['location_id']} if row['location_id'] else {'user_id': row['user_id']}
            if not party.get('location_id') and not party.get('user_id'):
                continue
            balance = row['available']
            if balance > 0:
                options.append({'ware': row['ware_id'],
                                'ware_name': row['ware__name_fa'] or row['ware__name_en'] or str(row['ware_id']),
                                'source_type': 'LOCATION' if row['location_id'] else 'USER',
                                'source_id': row['location_id'] or row['user_id'],
                                'source_name': row['location__name_fa'] or row['user__username'] or '',
                                'available': balance})
        return Response(options)

    def post(self, request, id):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        if not Ware.objects.filter(pk=values['ware'], project_id=access.project_id).exists():
            raise ValidationError({'ware': 'کالا در پروژه انتخاب‌شده نیست.'})
        source = {'ware': values['ware'], 'amount': -values['quantity'], 'side': 'FROM',
                  'involved': values['source_type'],
                  'location': values['source_id'] if values['source_type'] == 'LOCATION' else None,
                  'user': values['source_id'] if values['source_type'] == 'USER' else None}
        destination = {'ware': values['ware'], 'amount': values['quantity'], 'side': 'TO',
                       'involved': None, 'location': None, 'user': None}
        with transaction.atomic():
            repair = access.repairs.select_for_update().filter(pk=id).first()
            if repair is None:
                raise NotFound()
            transfer, replayed = create_stock_transfer(request, self, {
                'lines': [source, destination],
                'description': f'مصرف {values["quantity"]} کالا برای تعمیر {repair.rma_key}',
                'kind': 'CONSUME',
                'request_key': values['request_key'],
            })
            if replayed and transfer.repair_case_id != repair.pk:
                raise ValidationError({'request_key': 'این کلید برای انتقال دیگری استفاده شده است.'})
            if not replayed:
                if repair.status != RepairCase.REPAIRING:
                    raise ValidationError({'status': 'مصرف قطعه فقط در مرحله تعمیر ثبت می‌شود.'})
                transfer.repair_case = repair
                transfer.save(update_fields=['repair_case'])
                RepairEvent.objects.create(case=repair, from_status=repair.status,
                                           to_status=repair.status, actor=request.user,
                                           note=f'مصرف {values["quantity"]} کالا از موجودی ثبت شد.')
        return Response(RepairCaseSerializer(repair).data)


class RepairTransitionInput(serializers.Serializer):
    to_status = serializers.ChoiceField(choices=tuple(state for state, _ in RepairCase.STATUS_CHOICES))
    note = serializers.CharField(required=False, allow_blank=True, default='')
    diagnosis = serializers.CharField(required=False, allow_blank=True)
    work_performed = serializers.CharField(required=False, allow_blank=True)
    test_result = serializers.CharField(required=False, allow_blank=True)


ALLOWED_REPAIR_TRANSITIONS = {
    RepairCase.RECEIVED: {RepairCase.DIAGNOSING, RepairCase.CANCELED},
    RepairCase.DIAGNOSING: {RepairCase.REPAIRING, RepairCase.CANCELED},
    RepairCase.REPAIRING: {RepairCase.TESTING, RepairCase.CANCELED},
    RepairCase.TESTING: {RepairCase.REPAIRING, RepairCase.READY, RepairCase.CANCELED},
    RepairCase.READY: {RepairCase.DELIVERED, RepairCase.CANCELED},
}


class RepairCaseTransitionView(generics.GenericAPIView):
    serializer_class = RepairTransitionInput
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, id):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        with transaction.atomic():
            repair = access.repairs.select_for_update().filter(pk=id).first()
            if repair is None:
                raise NotFound()
            to_status = values['to_status']
            if to_status not in ALLOWED_REPAIR_TRANSITIONS.get(repair.status, set()):
                raise ValidationError({'to_status': 'این جابه‌جایی وضعیت مجاز نیست.'})
            for field in ('diagnosis', 'work_performed', 'test_result'):
                if field in values:
                    setattr(repair, field, values[field])
            if to_status == RepairCase.REPAIRING and not repair.diagnosis.strip():
                raise ValidationError({'diagnosis': 'تشخیص پیش از شروع تعمیر لازم است.'})
            if to_status == RepairCase.TESTING and not repair.work_performed.strip():
                raise ValidationError({'work_performed': 'کار انجام‌شده پیش از آزمون لازم است.'})
            if to_status == RepairCase.READY and not repair.test_result.strip():
                raise ValidationError({'test_result': 'نتیجه آزمون پیش از آماده‌سازی لازم است.'})
            old_status = repair.status
            repair.status = to_status
            if to_status == RepairCase.DELIVERED:
                repair.delivered_at = timezone.now()
            repair.save()
            event = RepairEvent.objects.create(case=repair, from_status=old_status,
                                               to_status=to_status, note=values['note'], actor=request.user)
            notify_repair_event(repair, event)
        return Response(RepairCaseSerializer(repair).data)


class RepairLoanerInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=('assign', 'return'))
    product = serializers.IntegerField(required=False, min_value=1)
    due_at = serializers.DateField(required=False)


class RepairCaseLoanerView(generics.GenericAPIView):
    serializer_class = RepairLoanerInput
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request, id):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        repair = access.repairs.filter(pk=id).first()
        if repair is None:
            raise NotFound()
        loaned = RepairCase.objects.filter(loaner_product__isnull=False,
                                           loaner_returned_at__isnull=True).values('loaner_product_id')
        products = Product.objects.filter(project_id=access.project_id).exclude(
            pk=repair.product_id,
        ).exclude(productelevator__is_active=True).exclude(
            pk__in=loaned,
        ).distinct().order_by('id')
        return Response([{'id': row.id, 'serial_number': row.serial_number or ''}
                         for row in products])

    def post(self, request, id):
        access = ServiceCaseAccess(request, self)
        access.require_manager()
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        with transaction.atomic():
            repair = access.repairs.select_for_update().filter(pk=id).first()
            if repair is None:
                raise NotFound()
            if repair.status in (RepairCase.DELIVERED, RepairCase.CANCELED):
                raise ValidationError({'action': 'پرونده بسته است.'})
            if values['action'] == 'assign':
                if 'product' not in values or 'due_at' not in values:
                    raise ValidationError({'product': 'قطعه امانی و موعد برگشت لازم‌اند.'})
                if repair.loaner_product_id is not None and repair.loaner_returned_at is None:
                    raise ValidationError({'product': 'برای این پرونده قطعه امانی فعال وجود دارد.'})
                loaner = Product.objects.select_for_update().filter(
                    pk=values['product'], project_id=access.project_id,
                ).first()
                if loaner is None or loaner.pk == repair.product_id:
                    raise ValidationError({'product': 'قطعه امانی معتبر نیست.'})
                if ProductElevator.objects.filter(product=loaner, is_active=True).exists():
                    raise ValidationError({'product': 'این قطعه روی آسانسور دیگری نصب است.'})
                if values['due_at'] < timezone.localdate():
                    raise ValidationError({'due_at': 'موعد برگشت باید امروز یا بعد از آن باشد.'})
                if RepairCase.objects.filter(loaner_product=loaner,
                                             loaner_returned_at__isnull=True).exclude(pk=repair.pk).exists():
                    raise ValidationError({'product': 'این قطعه امانی در پرونده دیگری فعال است.'})
                repair.loaner_product = loaner
                repair.loaner_due_at = values['due_at']
                repair.loaner_returned_at = None
                note = 'برد امانی تحویل شد.'
            else:
                if repair.loaner_product_id is None or repair.loaner_returned_at is not None:
                    raise ValidationError({'action': 'قطعه امانی فعالی برای برگشت وجود ندارد.'})
                repair.loaner_returned_at = timezone.now()
                note = 'برد امانی بازگردانده شد.'
            repair.save(update_fields=['loaner_product', 'loaner_due_at', 'loaner_returned_at'])
            RepairEvent.objects.create(case=repair, from_status=repair.status,
                                       to_status=repair.status, note=note, actor=request.user,
                                       loaner_product=repair.loaner_product,
                                       loaner_due_at=repair.loaner_due_at)
        return Response(RepairCaseSerializer(repair).data)
