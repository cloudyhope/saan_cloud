"""One atomic, replay-safe creation of a catalog item and its opening balance."""
import hashlib
import json
import uuid

from django.db import transaction
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_app.models import Project
from auth_app.permissions import authorized_role_views
from visit.models import VisitType
from warehouse.models import (Unit, Ware, WareType, WareVisitType,
                              WarehouseLocation, WarehouseTransaction)
from warehouse.stock import create_stock_transfer


class OpeningStockInput(serializers.Serializer):
    name_fa = serializers.CharField(max_length=255)
    name_en = serializers.CharField(required=False, allow_blank=True, max_length=255, default='')
    identifier = serializers.CharField(required=False, allow_blank=True, max_length=20, default='')
    description = serializers.CharField(required=False, allow_blank=True, default='')
    type = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    unit = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    is_for_use = serializers.BooleanField(default=False)
    quantity = serializers.IntegerField(min_value=1, max_value=2147483647)
    location = serializers.IntegerField(min_value=1)
    visit_types = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False,
                                       allow_empty=True, default=list)
    request_key = serializers.UUIDField()


class WareOpeningStockView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OpeningStockInput

    def post(self, request):
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise ValidationError({'p': 'پروژه معتبر لازم است.'})
        if project_id <= 0:
            raise ValidationError({'p': 'پروژه معتبر لازم است.'})
        for view_name in ('WareListCreateView', 'WareTransactionEzCreateView'):
            if not authorized_role_views(request, self, view_name=view_name).filter(
                    role__asset_scope='project').exists():
                raise PermissionDenied('ساخت کالا و موجودی نیازمند مجوز مدیریت انبار است.')
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        canonical = {field: str(value) if isinstance(value, uuid.UUID) else value
                     for field, value in values.items() if field != 'request_key'}
        canonical['visit_types'] = sorted(set(canonical['visit_types']))
        content_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True,
                                                 ensure_ascii=False).encode('utf-8')).hexdigest()
        with transaction.atomic():
            if not Project.objects.select_for_update().filter(pk=project_id, is_active=True).exists():
                raise ValidationError({'p': 'پروژه فعال پیدا نشد.'})
            prior = Ware.objects.filter(project_id=project_id, creation_key=values['request_key']).first()
            if prior is not None:
                if prior.creation_hash != content_hash:
                    raise ValidationError({'request_key': 'این کلید برای کالای دیگری استفاده شده است.'})
                transfer_key = uuid.uuid5(uuid.NAMESPACE_URL, f'saan/opening-stock/{values["request_key"]}')
                entry = WarehouseTransaction.objects.filter(project_id=project_id,
                                                             creator=request.user,
                                                             request_key=transfer_key).first()
                if entry is None:
                    raise ValidationError({'request_key': 'گردش افتتاح موجودی برای این کالا یافت نشد.'})
                return Response({'id': prior.pk, 'transaction_id': entry.pk, 'replayed': True})
            if not WarehouseLocation.objects.filter(pk=values['location'], projects__id=project_id).exists():
                raise ValidationError({'location': 'انبار در پروژه انتخاب‌شده نیست.'})
            if values.get('type') and not WareType.objects.filter(pk=values['type']).exists():
                raise ValidationError({'type': 'نوع کالا معتبر نیست.'})
            if values.get('unit') and not Unit.objects.filter(pk=values['unit']).exists():
                raise ValidationError({'unit': 'واحد کالا معتبر نیست.'})
            visit_types = list(dict.fromkeys(values['visit_types']))
            if VisitType.objects.filter(pk__in=visit_types, project_id=project_id).count() != len(visit_types):
                raise ValidationError({'visit_types': 'نوع بازدید باید در پروژه انتخاب‌شده باشد.'})
            ware = Ware.objects.create(
                project_id=project_id, creation_key=values['request_key'], creation_hash=content_hash,
                name_fa=values['name_fa'], name_en=values['name_en'], identifier=values['identifier'],
                description=values['description'], type_id=values.get('type'), unit_id=values.get('unit'),
                is_for_use=values['is_for_use'],
            )
            transfer_key = uuid.uuid5(uuid.NAMESPACE_URL, f'saan/opening-stock/{values["request_key"]}')
            quantity = values['quantity']
            entry, _ = create_stock_transfer(request, self, {
                'lines': [
                    {'ware': ware.pk, 'amount': -quantity, 'side': 'FROM', 'involved': None},
                    {'ware': ware.pk, 'amount': quantity, 'side': 'TO',
                     'involved': 'LOCATION', 'location': values['location']},
                ],
                'description': f'افتتاح موجودی {quantity} واحد برای {ware.name_fa}',
                'kind': 'OPENING',
                'request_key': transfer_key,
            }, permission_view_name='WareTransactionEzCreateView')
            WareVisitType.objects.bulk_create([
                WareVisitType(ware=ware, visit_type_id=visit_type_id)
                for visit_type_id in visit_types
            ])
        return Response({'id': ware.pk, 'transaction_id': entry.pk, 'replayed': False}, status=201)
