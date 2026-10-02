"""Project-scoped, balanced warehouse transfers over the existing signed ledger."""
import hashlib
import json

from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from auth_app.models import RoleAssignment
from auth_app.permissions import authorized_role_views
from warehouse.models import (TransactionLineType, Ware, WarehouseLocation,
                              WarehouseTransaction, WarehouseTransactionLine)


class TransferLineInput(serializers.Serializer):
    ware = serializers.IntegerField(min_value=1)
    amount = serializers.IntegerField(min_value=-2147483647, max_value=2147483647)
    side = serializers.ChoiceField(choices=('FROM', 'TO'))
    involved = serializers.ChoiceField(choices=('LOCATION', 'USER'), allow_null=True, required=False)
    location = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    user = serializers.IntegerField(min_value=1, allow_null=True, required=False)


class StockTransferInput(serializers.Serializer):
    lines = TransferLineInput(many=True, min_length=2, max_length=2)
    description = serializers.CharField(required=False, allow_blank=True, max_length=2000, default='')
    request_key = serializers.UUIDField()
    visit = serializers.IntegerField(required=False, min_value=1)
    kind = serializers.ChoiceField(choices=(
        'RECEIPT', 'OPENING', 'TRANSFER', 'RETURN', 'CONSUME', 'SCRAP'), required=False)

    def validate_lines(self, lines):
        source, destination = lines
        if (source['side'] != 'FROM' or destination['side'] != 'TO'
                or source['ware'] != destination['ware']
                or source['amount'] >= 0 or destination['amount'] <= 0
                or source['amount'] + destination['amount'] != 0):
            raise ValidationError('انتقال باید دو ردیف هم‌مقدار، کاهشی و افزایشی برای یک کالا داشته باشد.')
        for line in lines:
            involved = line.get('involved')
            location, user = line.get('location'), line.get('user')
            if ((involved == 'LOCATION' and (location is None or user is not None))
                    or (involved == 'USER' and (user is None or location is not None))
                    or (involved is None and (location is not None or user is not None))):
                raise ValidationError('مالک ردیف باید یک انبار، یک کاربر یا سمت بیرونی باشد.')
        if (source.get('involved'), source.get('location'), source.get('user')) == (
                destination.get('involved'), destination.get('location'), destination.get('user')):
            raise ValidationError('مبدأ و مقصد نمی‌توانند یکسان باشند.')
        return lines

    def validate(self, attrs):
        attrs['kind'] = movement_kind(attrs)
        return attrs


def movement_kind(values):
    source, destination = values['lines']
    source_party, destination_party = source.get('involved'), destination.get('involved')
    if source_party is None and destination_party in ('LOCATION', 'USER'):
        inferred = 'RECEIPT'
    elif source_party == 'USER' and destination_party == 'LOCATION':
        inferred = 'RETURN'
    elif source_party in ('LOCATION', 'USER') and destination_party is None:
        inferred = 'CONSUME'
    else:
        inferred = 'TRANSFER'
    kind = values.get('kind') or inferred
    allowed = {
        'RECEIPT': source_party is None and destination_party in ('LOCATION', 'USER'),
        'OPENING': source_party is None and destination_party == 'LOCATION',
        'TRANSFER': source_party in ('LOCATION', 'USER') and destination_party in ('LOCATION', 'USER')
                    and not (source_party == 'USER' and destination_party == 'LOCATION'),
        'RETURN': source_party == 'USER' and destination_party == 'LOCATION',
        'CONSUME': source_party in ('LOCATION', 'USER') and destination_party is None,
        'SCRAP': source_party in ('LOCATION', 'USER') and destination_party is None,
    }
    if not allowed.get(kind):
        raise ValidationError({'kind': 'نوع گردش با مبدأ و مقصد هم‌خوان نیست.'})
    if kind in ('RETURN', 'SCRAP') and len((values.get('description') or '').strip()) < 10:
        raise ValidationError({'description': 'دلیل برگشت یا ضایعات باید حداقل ۱۰ نویسه باشد.'})
    return kind


def _party_filter(line):
    if line.get('involved') == 'LOCATION':
        return {'location_id': line['location'], 'user_id__isnull': True}
    return {'user_id': line['user'], 'location_id__isnull': True}


def _validate_party(line, project_id):
    involved = line.get('involved')
    if involved == 'LOCATION':
        if not WarehouseLocation.objects.filter(pk=line['location'], projects__id=project_id).exists():
            raise ValidationError({'location': 'انبار به پروژه انتخاب‌شده تعلق ندارد.'})
    elif involved == 'USER':
        if not RoleAssignment.objects.filter(user_id=line['user'], project_id=project_id,
                                             is_deleted=False, user__is_active=True,
                                             role__is_active=True).exists():
            raise ValidationError({'user': 'کاربر در پروژه عضویت فعال ندارد.'})


def create_stock_transfer(request, view, values, permission_view_name=None):
    try:
        project_id = int(request.query_params.get('p'))
    except (TypeError, ValueError):
        raise PermissionDenied('پروژه معتبر لازم است.')
    if project_id <= 0:
        raise PermissionDenied('پروژه معتبر لازم است.')
    scopes = set(authorized_role_views(request, view, view_name=permission_view_name).values_list(
        'role__asset_scope', flat=True))
    source, destination = values['lines']
    kind = movement_kind(values)
    if 'project' not in scopes:
        if not (kind == 'CONSUME' and {'assigned', 'supervised'} & scopes and source.get('involved') == 'USER'
                and source.get('user') == request.user.pk and destination.get('involved') is None):
            raise PermissionDenied('انتقال موجودی نیازمند نقش مدیریتی پروژه است.')
    canonical = {'lines': [{key: line.get(key) for key in ('ware', 'amount', 'side', 'involved', 'location', 'user')}
                           for line in values['lines']], 'description': values['description'],
                 'visit': values.get('visit')}
    legacy_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True,
                                             ensure_ascii=False).encode('utf-8')).hexdigest()
    canonical['kind'] = kind
    payload_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True,
                                             ensure_ascii=False).encode('utf-8')).hexdigest()
    with transaction.atomic():
        ware = Ware.objects.select_for_update().filter(pk=source['ware'], project_id=project_id).first()
        if ware is None:
            raise ValidationError({'ware': 'کالا در پروژه انتخاب‌شده نیست.'})
        key = values['request_key']
        prior = WarehouseTransaction.objects.filter(project_id=project_id,
                                                    creator=request.user, request_key=key).first()
        if prior is not None:
            if prior.payload_hash != payload_hash and not (
                    prior.payload_hash == legacy_hash and prior.movement_kind == WarehouseTransaction.LEGACY
                    and kind == movement_kind({**values, 'kind': None})):
                raise ValidationError({'request_key': 'این کلید برای انتقال دیگری استفاده شده است.'})
            return prior, True
        if not ware.is_active:
            raise ValidationError({'ware': 'کالا در پروژه انتخاب‌شده فعال نیست.'})
        if 'project' not in scopes:
            from visit.models import Visit
            from visit.asset_access import AssetAccess
            visit_id = values.get('visit')
            access = AssetAccess(request, view)
            if not visit_id or not access.assigned_visits.filter(pk=visit_id).exists():
                raise PermissionDenied('مصرف نیروی اجرایی باید به بازدید تخصیص‌یافته متصل باشد.')
            if not Ware.objects.filter(pk=ware.pk, warevisittype__visit_type_id__in=
                                       Visit.objects.filter(pk=visit_id).values('type_id')).exists():
                raise ValidationError({'ware': 'این کالا برای نوع بازدید انتخاب‌شده مجاز نیست.'})
        for line in values['lines']:
            _validate_party(line, project_id)
        if source.get('involved') is not None:
            balance = WarehouseTransactionLine.objects.filter(ware=ware,
                        **_party_filter(source)).aggregate(total=Sum('amount'))['total'] or 0
            if balance < -source['amount']:
                raise ValidationError({'amount': 'موجودی مبدأ برای این انتقال کافی نیست.'})
        entry = WarehouseTransaction.objects.create(project_id=project_id, creator=request.user,
                                                     description=values['description'],
                                                     movement_kind=kind,
                                                     request_key=key, payload_hash=payload_hash)
        for line in values['lines']:
            involved = line.get('involved')
            kind = TransactionLineType.objects.filter(side=line['side'], involved=involved).first()
            if kind is None:
                kind = TransactionLineType.objects.create(side=line['side'], involved=involved,
                                                          name=f'{line["side"]} {involved or "EXTERNAL"}')
            WarehouseTransactionLine.objects.create(
                transaction=entry, ware=ware, amount=line['amount'], type=kind,
                location_id=line.get('location'), user_id=line.get('user'),
            )
        return entry, False
