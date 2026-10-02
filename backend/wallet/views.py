from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from auth_app.permissions import DeleteCreateUpdateGetPermission
from django.utils.translation import gettext_lazy as _
from wallet.models import (
    Currency,
    Layer,
    WalletType,
    Account,
    Wallet,
    TransactionType,
    AllowedTransactionRule,
    WalletTransaction,
    RefTransaction,
    TransactionLineType,
    WalletTransactionLine,
    WalletInvoice,
    CodeForWalletInvoice,
)
# Create your views here.
from core.modules.views import (
    List, 
    Create,
    ListCreate,
    Retrieve,
    Update,
    Destroy,
    RetrieveDestroy,
    RetrieveUpdate,
    RetrieveUpdateDestroy,
    Generic,
    APIView,
    )

from wallet.serializers import (
    CurrencySerializer,
    LayerSerializer,
    WalletTypeSerializer,
    AccountSerializer,
    OnlyAccountSerializer,
    WalletSerializer,
    TransactionTypeSerializer,
    AllowedTransactionRuleSerializer,
    OnlyAllowedTransactionRuleSerializer,
    OnlyWalletSerializer,
    WalletTransactionSerializer,
    WalletTransactionToggleReverseSerializer,
    OnlyWalletTransactionSerializer,
    RefTransactionSerializer,
    WalletTransactionLineTypeSerializer,
    WalletTransactionLineSerializer,
    OnlyWalletTransactionLineSerializer,
    WalletGetSignatureSerializer,
    WalletBalanceSerializer,
    WalletPlaceTransactionSerializer,
    CreateWalletForUserSerializer,
    OnlyWalletInvoiceSerializer,
    WalletInvoiceSerializer,
    NestedCodeForWalletInvoiceSerializer,
    CreateWalletInvoiceSerializer,
    InvoiceCodeRequestSerializer,
    InvoiceCodeValidateSerializer,
    WalletInvoiceReceiptSerializer,
    StoreWalletInvoiceSerializer, 
    WalletTransactionLineGroupByLayerSerializer,
    ChargeWalletByUsernameSerializer,
)

######################################
# ListCreate:
######################################

class CurrencyListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Currency.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CurrencySerializer
        else:
            return CurrencySerializer

class LayerListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Layer.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LayerSerializer
        else:
            return LayerSerializer

class WalletTypeListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return WalletType.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTypeSerializer
        else:
            return WalletTypeSerializer

class AccountListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Account.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AccountSerializer
        else:
            return OnlyAccountSerializer

class WalletListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Wallet.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletSerializer
        else:
            return OnlyWalletSerializer

class TransactionTypeListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return TransactionType.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransactionTypeSerializer
        else:
            return TransactionTypeSerializer

class AllowedTransactionRuleListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return AllowedTransactionRule.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AllowedTransactionRuleSerializer
        else:
            return OnlyAllowedTransactionRuleSerializer

class WalletTransactionListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return WalletTransaction.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTransactionSerializer
        else:
            return OnlyWalletTransactionSerializer

class RefTransactionListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return RefTransaction.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RefTransactionSerializer
        else:
            return RefTransactionSerializer

class WalletTransactionLineTypeListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return TransactionLineType.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTransactionLineTypeSerializer
        else:
            return WalletTransactionLineTypeSerializer

class WalletTransactionLineListCreateView(ListCreate):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return WalletTransactionLine.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTransactionLineSerializer
        else:
            return OnlyWalletTransactionLineSerializer



######################################
# Edits:
######################################


class CurrencyEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Currency.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CurrencySerializer
        else:
            return CurrencySerializer

class LayerEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Layer.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LayerSerializer
        else:
            return LayerSerializer

class WalletTypeEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return WalletType.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTypeSerializer
        else:
            return WalletTypeSerializer

class AccountEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Account.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AccountSerializer
        else:
            return OnlyAccountSerializer

class WalletEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return Wallet.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletSerializer
        else:
            return OnlyWalletSerializer
        
class TransactionTypeEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return TransactionType.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransactionTypeSerializer
        else:
            return TransactionTypeSerializer

class AllowedTransactionRuleEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return AllowedTransactionRule.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AllowedTransactionRuleSerializer
        else:
            return OnlyAllowedTransactionRuleSerializer

class WalletTransactionEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return WalletTransaction.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTransactionSerializer
        else:
            return OnlyWalletTransactionSerializer

class RefTransactionEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return RefTransaction.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RefTransactionSerializer
        else:
            return RefTransactionSerializer

class WalletTransactionLineTypeEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return TransactionLineType.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTransactionLineTypeSerializer
        else:
            return WalletTransactionLineTypeSerializer

class WalletTransactionLineEditsView(RetrieveUpdateDestroy):
    http_method_names = ['get', 'head', 'options']
    permission_classes = [IsAdminUser, DeleteCreateUpdateGetPermission]
    def get_queryset(self):
        return WalletTransactionLine.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletTransactionLineSerializer
        else:
            return OnlyWalletTransactionLineSerializer


##############################
# Custom apis:
##############################

class WalletGetSignatureView(Generic):
    serializer_class = WalletBalanceSerializer
    def get(self, request, *args, **kwargs):
        account = Account.objects.filter(user=request.user).first()
        if account is None:
            from auth_app.serializers import LiteUserSerializer
            return Response({'user': LiteUserSerializer(request.user).data, 'wallets': []})
        return Response(self.get_serializer(account).data)

# from auth_app.permissions import DeleteCreateUpdateGetPermission
from rest_framework import views as drf_views
class ChargeWalletByUsernameView(APIView):
    serializer_class = ChargeWalletByUsernameSerializer
    # permission_classes = [
    #     DeleteCreateUpdateGetPermission,
    # ]

    # def get_queryset(self):
    #     return User.objects.none()

    # def get(self, request):
    #     return Response({})

    def post(self, request, *args, **kwargs):
        lc_users = LCUser.objects.filter(user__username=self.request.data['username'])
        lc_user = lc_users.first()
        # Logic of charge!
        from config.models import Config
        provider_charge_credit_transaction_type_key = Config.objects.get(key="PROVIDER_CHARGE_CREDIT_TRANSACTION_TYPE_KEY").value
        # provider_charge_credit_wallet_public_address = Config.objects.get(key="PROVIDER_CHARGE_CREDIT_WALLET_PUBLIC_ADDRESS").value
        provider_charge_credit_layer_key = Config.objects.get(key="PROVIDER_CHARGE_CREDIT_LAYER_KEY").value
        provider_charge_credit_customer_wallet_type_key = Config.objects.get(key="PROVIDER_CHARGE_CREDIT_CUSTOMER_WALLET_TYPE_KEY").value
           
        from wallet.models import Wallet
        from wallet.core import WalletCore
        core = WalletCore()
        core.create_wallet_for_user_if_not_exists(lc_user.user, provider_charge_credit_customer_wallet_type_key)
        to_wallet_address = Wallet.objects.get(account__user=lc_user.user, type__key=provider_charge_credit_customer_wallet_type_key).public_address

        transaction = core.place_transaction(
            {
                "creator": self.request.user,
                "amount": self.request.data['amount'],
                "from": None,
                "to": to_wallet_address,
                "currency": "IRR",
                "layer": provider_charge_credit_layer_key,
                "transaction_type": provider_charge_credit_transaction_type_key,
                "description": "",
                "ref": {
                    "data": None
                }
            }
        )
        return Response(transaction) 

# class WalletPlaceTransactionView(Generic):
#     serializer_class = WalletPlaceTransactionSerializer
#     def post(self, request, *args, **kwargs):
#         from wallet.secrets import WalletCrypt
#         crypt = WalletCrypt()
#         # Decryption:
#         raw_msg = crypt.static_decrypt(self.request.data['data'])
#         signature = self.request.data['signature']
#         # Checking signature:
#         if not crypt.validate_signature(Account.objects.get(user=self.request.user).signature_identifier, signature, raw_msg):
#             from core.modules.exceptions import BadRequest
#             raise BadRequest("Invalid Signature!")
        
#         # Calling the WalletCore:
#         from wallet.core import WalletCore
#         import json
#         core = WalletCore()
#         dict_data = json.loads(raw_msg)
#         required_fields = ["amount", "from", "layer", "currency", "to", "transaction_type"]
#         for required_field in required_fields:
#             if required_field not in dict_data.keys():
#                 raise BadRequest("field '" + required_field + "' is required!")
#         transaction_id = core.place_transaction(dict_data)
#         return Response({"transaction_id": transaction_id})

        
class WalletPlaceTransactionView(Generic):
    serializer_class = WalletPlaceTransactionSerializer
    permission_classes = [
        IsAdminUser,
    ]
    def post(self, request, *args, **kwargs):
        raw_msg = self.request.data['data']
        # Calling the WalletCore:
        from wallet.core import WalletCore
        import json
        core = WalletCore()
        # dict_data = json.loads(raw_msg)
        dict_data = raw_msg
        from django.contrib.auth import get_user_model
        User = get_user_model()
        dict_data['creator'] = User.objects.get(id=self.request.user.id)
        required_fields = ["creator", "amount", "from", "layer", "currency", "to", "transaction_type"]
        for required_field in required_fields:
            if required_field not in dict_data.keys():
                from core.modules.exceptions import BadRequest
                raise BadRequest(_("field '%(required_field)' is required!") % required_field)
        transaction_id = core.place_transaction(dict_data, forced=True)
        return Response({"transaction_id": transaction_id})

        

class WalletAccountsHyperListView(List):
    serializer_class = WalletGetSignatureSerializer
    def get_queryset(self):
        return Account.objects.all()
    
    
class CreateWalletForUserView(Generic):
    def get_queryset(self):
        return Wallet.objects.none()
    serializer_class = CreateWalletForUserSerializer

    def post(self, request, *args, **kwargs):
        from wallet.core import WalletCore
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(username=self.request.data['username'])
        core = WalletCore()
        wallet = core.create_wallet_for_user(user, self.request.data['wallet_type_key'], self.request.data['short_address'])
        return Response(WalletSerializer(wallet, many=False).data)


class WalletInvoiceExpertListCreateView(ListCreate):

    def get_queryset(self):
        from auth_app.permissions import authorized_role_views
        from rest_framework.exceptions import PermissionDenied
        if not authorized_role_views(self.request, self).filter(
                role__asset_scope__in=('assigned', 'supervised')).exists():
            raise PermissionDenied('دسترسی به فاکتورهای کارشناس مجاز نیست.')
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return WalletInvoice.objects.none()
        return WalletInvoice.objects.filter(
            expert=self.request.user, visit__type__project_id=project_id,
            visit__building__project_id=project_id)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WalletInvoiceSerializer
        return CreateWalletInvoiceSerializer
    
    def perform_create(self, serializer):
        import hashlib
        import json
        from django.db import IntegrityError, transaction
        from rest_framework.exceptions import ValidationError
        from auth_app.models import RoleAssignment
        from auth_app.permissions import authorized_role_views
        from visit.management import current_management_q
        from visit.models import BuildingClient, UserClient
        from visit.views import assigned_field_visit
        if not authorized_role_views(self.request, self).filter(
                role__asset_scope__in=('assigned', 'supervised')).exists():
            raise ValidationError({'visit': 'دسترسی به صدور فاکتور مجاز نیست.'})
        visit = assigned_field_visit(self.request, serializer.validated_data['visit'].pk, view=self)
        request_key = serializer.validated_data['request_key']
        payload = {
            'visit': visit.pk, 'project': visit.type.project_id,
            'amount_rials': serializer.validated_data['amount_rials'],
            'type': serializer.validated_data['type'],
            'description': serializer.validated_data.get('description') or '',
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
        existing = WalletInvoice.objects.filter(expert=self.request.user, request_key=request_key).first()
        if existing:
            if existing.payload_hash != digest:
                raise ValidationError({'request_key': 'این کلید قبلاً با محتوای دیگری استفاده شده است.'})
            serializer.instance = existing
            return existing
        managers = list(BuildingClient.objects.filter(
            building=visit.building, client__project_id=visit.type.project_id,
        ).filter(current_management_q()).values_list('client_id', flat=True).distinct())
        if len(managers) != 1:
            raise ValidationError({'visit': 'مدیر فعلی ساختمان برای صدور فاکتور یکتا نیست.'})
        eligible_users = RoleAssignment.objects.filter(
            project_id=visit.type.project_id, project__is_active=True,
            is_deleted=False, role__is_active=True, role__asset_scope='client',
            user__is_active=True,
            user_id__in=UserClient.objects.filter(client_id=managers[0]).values('user_id'),
        ).values_list('user_id', flat=True).distinct()
        recipient_ids = list(eligible_users)
        if len(recipient_ids) != 1:
            raise ValidationError({'visit': 'گیرنده فاکتور مشخص نیست؛ نماینده مشتری باید یکتا باشد.'})
        from django.contrib.auth import get_user_model
        client = get_user_model().objects.get(pk=recipient_ids[0])
        try:
            with transaction.atomic():
                instance = serializer.save(client=client, expert=self.request.user,
                                           visit=visit, payload_hash=digest)
                transaction.on_commit(lambda: self._notify_created_invoice(instance.pk))
        except IntegrityError:
            existing = WalletInvoice.objects.filter(expert=self.request.user, request_key=request_key).first()
            if existing is None or existing.payload_hash != digest:
                raise ValidationError({'request_key': 'این کلید قبلاً با محتوای دیگری استفاده شده است.'})
            serializer.instance = existing
            return existing
        return instance

    @staticmethod
    def _notify_created_invoice(invoice_id):
        import logging
        from notification.modules.notification import Notification
        from notification.modules.tools import flatten_dict
        instance = WalletInvoice.objects.select_related('expert', 'client').get(pk=invoice_id)
        data = flatten_dict(WalletInvoiceSerializer(instance).data)
        for user, template in ((instance.expert, 'EXPERT_CREATE_INVOICE'),
                               (instance.client, 'CLIENT_CREATE_INVOICE')):
            try:
                Notification(to=user.username, message_template_key=template, **data)
            except Exception:
                logging.getLogger(__name__).exception('Invoice notification failed')

from rest_framework.permissions import IsAuthenticated
class WalletInvoiceGetQRCodeView(Retrieve):
    def get_queryset(self):
        from auth_app.models import RoleAssignment, RoleView
        from django.db.models import Q
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return WalletInvoice.objects.none()
        invoice_roles = RoleView.objects.filter(
            view_method_name__view_name='WalletInvoiceExpertListCreateView',
            view_method_name__method='POST', can_create=True,
        ).values('role_id')
        if project_id <= 0 or not RoleAssignment.objects.filter(
                user=self.request.user, project_id=project_id, is_deleted=False,
                project__is_active=True, role__is_active=True,
                role__asset_scope__in=('assigned', 'supervised'),
                role_id__in=invoice_roles).exists():
            return WalletInvoice.objects.none()
        return WalletInvoice.objects.filter(
            expert=self.request.user, visit__type__project_id=project_id,
            visit__building__project_id=project_id, is_closed=False,
        ).filter(Q(visit__expert=self.request.user) | Q(visit__promoter=self.request.user))
    def get_serializer_class(self):
        return WalletInvoiceSerializer
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        import qrcode
        from io import BytesIO
        from config.models import Config
        base = Config.objects.filter(key='QR_WALLET_INVOICE_BASE_ADDRESS').values_list('value', flat=True).first()
        if not base:
            return Response({'detail': 'نشانی کد پرداخت تنظیم نشده است.'}, status=503)
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=8, border=4)
        qr.add_data(base + str(instance.id))
        qr.make(fit=True)
        pill_img = qr.make_image(fill_color='black', back_color='white')
        buffered = BytesIO()
        pill_img.save(buffered, format='PNG')
        from django.http import HttpResponse
        response =  HttpResponse(buffered.getvalue(), content_type='image/png')
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response

class WalletInvoiceClientRetrieveView(Retrieve):
    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return WalletInvoice.objects.none()
        return WalletInvoice.objects.filter(
            client=self.request.user, is_closed=False, status=WalletInvoice.STATUS.INITIAL,
            visit__type__project_id=project_id, visit__building__project_id=project_id,
        )
    def get_serializer_class(self):
        return WalletInvoiceSerializer

class WalletInvoiceCodeRequestView(Create):
    serializer_class = InvoiceCodeRequestSerializer

    def create(self, request, *args, **kwargs):
        import secrets
        from datetime import timedelta
        from django.contrib.auth.hashers import make_password
        from django.db import transaction
        from django.http import Http404
        from django.utils import timezone
        from rest_framework.exceptions import Throttled, ValidationError

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise Http404
        with transaction.atomic():
            invoice = WalletInvoice.objects.select_for_update().filter(
                pk=serializer.validated_data['wallet_invoice'], client=request.user,
                visit__type__project_id=project_id, visit__building__project_id=project_id,
                is_closed=False, status=WalletInvoice.STATUS.INITIAL,
            ).first()
            if invoice is None:
                raise Http404
            if invoice.type != WalletInvoice.TYPES.CREDIT or invoice.amount_rials <= 0:
                raise ValidationError({'wallet_invoice': 'این فاکتور برای پرداخت اعتباری معتبر نیست.'})
            last = CodeForWalletInvoice.objects.filter(wallet_invoice=invoice).order_by('-datetime_requested', '-pk').first()
            if last and last.datetime_requested and last.datetime_requested > timezone.now() - timedelta(seconds=60):
                raise Throttled(detail='برای درخواست کد جدید کمی صبر کنید.', wait=60)
            raw_code = str(10000 + secrets.randbelow(90000))
            code = CodeForWalletInvoice.objects.create(
                wallet_invoice=invoice, code_hash=make_password(raw_code))
            transaction.on_commit(lambda: self._notify_code(code.pk, raw_code))
        response = Response({
            'id': code.pk, 'wallet_invoice': str(invoice.pk),
            'verification_token': code.verification_token,
            'datetime_requested': code.datetime_requested,
        }, status=201)
        response['Cache-Control'] = 'private, no-store'
        return response

    @staticmethod
    def _notify_code(code_id, raw_code):
        import logging
        from notification.modules.notification import Notification
        from notification.modules.tools import flatten_dict
        code = CodeForWalletInvoice.objects.select_related('wallet_invoice__client').get(pk=code_id)
        try:
            details = flatten_dict(NestedCodeForWalletInvoiceSerializer(code).data)
            details['code'] = raw_code
            Notification(to=code.wallet_invoice.client.username,
                         message_template_key='CODE_FOR_WALLET_INVOICE', **details)
        except Exception:
            logging.getLogger(__name__).exception('Invoice code notification failed')


class WalletInvoiceCodeValidateView(Generic):
    serializer_class = InvoiceCodeValidateSerializer

    def post(self, request, *args, **kwargs):
        import secrets
        from datetime import timedelta
        from django.contrib.auth import get_user_model
        from django.contrib.auth.hashers import check_password
        from django.db import transaction
        from django.http import Http404
        from django.utils import timezone
        from rest_framework.exceptions import ValidationError
        from config.models import Config
        from wallet.core import WalletCore

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise Http404
        with transaction.atomic():
            invoice = WalletInvoice.objects.select_for_update().filter(
                pk=data['wallet_invoice'], client=request.user,
                visit__type__project_id=project_id, visit__building__project_id=project_id,
                is_closed=False, status=WalletInvoice.STATUS.INITIAL,
                type=WalletInvoice.TYPES.CREDIT,
            ).first()
            if invoice is None:
                raise Http404
            code = CodeForWalletInvoice.objects.select_for_update().filter(
                pk=data['id'], wallet_invoice=invoice,
            ).first()
            latest = CodeForWalletInvoice.objects.filter(wallet_invoice=invoice).order_by('-datetime_requested', '-pk').first()
            if code is None or latest is None or code.pk != latest.pk:
                raise ValidationError({'code': 'کد پرداخت معتبر نیست.'})
            if code.consumed_at or code.failed_attempts >= 5:
                raise ValidationError({'code': 'کد پرداخت دیگر معتبر نیست.'})
            if not code.datetime_requested or code.datetime_requested <= timezone.now() - timedelta(minutes=2):
                raise ValidationError({'code': 'زمان اعتبار کد پرداخت پایان یافته است.'})
            if not secrets.compare_digest(code.verification_token, data['verification_token']) or not check_password(data['code'], code.code_hash):
                code.failed_attempts += 1
                code.save(update_fields=['failed_attempts'])
                return Response({'detail': 'کد پرداخت نادرست است.'}, status=400)
            # The payer row serializes concurrent payments of separate invoices on PostgreSQL.
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            settings = dict(Config.objects.filter(key__in=(
                'QR_CREDIT_FROM_WALLET_TYPE_KEY', 'QR_CREDIT_TO_WALLET_TYPE_KEY',
                'QR_CREDIT_FROM_LAYER_TYPE_KEY', 'CREDIT_PAY_BY_QR_TRANSACTION_TYPE_KEY',
            )).values_list('key', 'value'))
            if len(settings) != 4 or not all(settings.values()):
                return Response({'detail': 'تنظیمات پرداخت کامل نیست.'}, status=503)
            core = WalletCore()
            try:
                result = core.place_transaction({
                    'creator': request.user, 'amount': invoice.amount_rials,
                    'from': core.safe_get_wallet(invoice.client, settings['QR_CREDIT_FROM_WALLET_TYPE_KEY']).public_address,
                    'to': core.safe_get_wallet(invoice.expert, settings['QR_CREDIT_TO_WALLET_TYPE_KEY']).public_address,
                    'currency': 'IRR', 'layer': settings['QR_CREDIT_FROM_LAYER_TYPE_KEY'],
                    'transaction_type': settings['CREDIT_PAY_BY_QR_TRANSACTION_TYPE_KEY'],
                    'description': invoice.description,
                    'ref': {'wallet_invoice': str(invoice.pk)},
                }, _COMMISSION=0)
            except ValueError as exc:
                raise ValidationError({'detail': str(exc)}) from exc
            transaction_id = result[1] if isinstance(result, tuple) and len(result) == 2 else None
            if not isinstance(transaction_id, int) or transaction_id <= 0 or not WalletTransaction.objects.filter(pk=transaction_id).exists():
                raise ValidationError({'detail': 'تراکنش ثبت نشد؛ فاکتور باز مانده است.'})
            invoice.is_closed = True
            invoice.status = WalletInvoice.STATUS.PAID
            invoice.save(update_fields=['is_closed', 'status', 'datetime_last_change'])
            code.consumed_at = timezone.now()
            code.save(update_fields=['consumed_at'])
            transaction.on_commit(lambda: self._notify_payment(invoice.pk))
        return Response({'status': True, 'transaction_id': transaction_id})

    @staticmethod
    def _notify_payment(invoice_id):
        import logging
        from notification.modules.notification import Notification
        from notification.modules.tools import flatten_dict
        invoice = WalletInvoice.objects.select_related('client', 'expert').get(pk=invoice_id)
        details = flatten_dict(WalletInvoiceSerializer(invoice).data)
        for recipient, template in ((invoice.client, 'CLIENT_APPROVED_WALLET_INVOICE'),
                                    (invoice.expert, 'EXPERT_APPROVED_WALLET_INVOICE')):
            try:
                Notification(to=recipient.username, message_template_key=template, **details)
            except Exception:
                logging.getLogger(__name__).exception('Invoice payment notification failed')


class WalletReceiptRetrieve(Retrieve):

    serializer_class = WalletInvoiceReceiptSerializer

    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return WalletInvoice.objects.none()
        return WalletInvoice.objects.filter(
            client=self.request.user, is_closed=True, status=WalletInvoice.STATUS.PAID,
            visit__type__project_id=project_id, visit__building__project_id=project_id,
        )


class WalletInvoiceStoreListView(List):

    def get_queryset(self):
        from loyalty.models.models import StoreLoyaltyPlanPersonel
        user_in_store = list(StoreLoyaltyPlanPersonel.objects.filter(user=self.request.user).values_list('store_loyalty_plan__store__id', flat=True))
        return WalletInvoice.objects.filter(store__id__in=user_in_store)

    serializer_class = WalletInvoiceSerializer

    filterset_fields = {
        'type': ['exact', 'in', ],
        'store__id': ['exact', 'in', ],
        'store_loyalty_plan__id': ['exact', 'in', ],
        'amount_rials': ['gte', 'lte', 'range',],
        'payable_amount_rials': ['gte', 'lte', 'range',],
        'is_closed': ['exact',],
        'datetime_created': ['exact', 'gte', 'lte', 'range', 'in'],
        'datetime_last_change': ['gte', 'lte', 'range', 'in', 'exact'],
        'status': ['exact',],
        'expert__username': ['exact', 'in', ],
        'client__username': ['exact', 'in', ],
        'store_loyalty_plan__is_active': ['exact'],
    }
class UserWalletTransactionLineList(List):

    serializer_class = WalletTransactionLineSerializer

    def get_queryset(self):
        return WalletTransactionLine.objects.filter(wallet__account__user=self.request.user)

    filterset_fields = {
        "amount": ["exact", "lte", "gte", "range",],
        "ref": ["exact", 'in',],
        'ref__wallet_invoice': ['exact',],
        'ref__wallet_invoice__expert': ['exact',],
        # 'ref__wallet_invoice__building': ['exact',],
        # 'ref__wallet_invoice__store_loyalty_plan': ['exact',],
        'ref__wallet_invoice__client': ['exact',],
        'ref__wallet_invoice__amount_rials': ['exact',],
        "layer": ['exact', 'in',],
        "type": ["exact", "in",],
        'type__id': ['exact', 'in',],
        "layer__priority": ["exact", "in",],
        "currency": ["exact", "in",],
        "transaction": ["exact", "in",],
        "transaction__description": ["exact",],
        "transaction__creator": ["exact",],
        "transaction__datetime_created": ["exact",],
        "transaction__datetime_last_change": ["exact",],
        "transaction__type": ["exact",],
        "transaction__type__name": ["exact",],
        'transaction__type__verbose_name': ['exact',],
        'currency__name_en': ['exact',],
        'currency__name_fa': ['exact',],
        'wallet': ['exact',],
        'wallet__type__name_fa': ['exact',],
        'wallet__type__name_en': ['exact',],

    }


class StoreWalletTransactionLineList(List):

    serializer_class = WalletTransactionLineSerializer

    def get_queryset(self):
        return WalletTransactionLine.objects.filter(wallet__account__user=self.request.user)

    filterset_fields = {
        "amount": ["exact", "lte", "gte", "range", ],
        "ref": ["exact", 'in', ],
        'ref__wallet_invoice': ['exact', ],
        'ref__wallet_invoice__expert': ['exact', ],
        'ref__wallet_invoice__store': ['exact', ],
        'ref__wallet_invoice__store_loyalty_plan': ['exact', ],
        'ref__wallet_invoice__client': ['exact', ],
        'ref__wallet_invoice__amount_rials': ['exact', ],
        "layer": ['exact', 'in', ],
        "type": ["exact", "in", ],
        'type__id': ['exact', 'in', ],
        "layer__priority": ["exact", "in", ],
        "currency": ["exact", "in", ],
        "transaction": ["exact", "in", ],
        "transaction__description": ["exact", ],
        "transaction__creator": ["exact", ],
        "transaction__datetime_created": ["exact", ],
        "transaction__datetime_updated": ["exact", ],
        "transaction__type": ["exact", ],
        "transaction__type__name": ["exact", ],
        'transaction__type__verbose_name': ['exact', ],
        'currency__name_en': ['exact', ],
        'currency__name_fa': ['exact', ],
        'wallet': ['exact', ],
        'wallet__type__name_fa': ['exact', ],
        'wallet__type__name_en': ['exact', ],

    }


class WalletTransactionToggleReverseView(Update):

    def get_queryset(self):
        return WalletTransaction.objects.all()
    
    serializer_class = WalletTransactionToggleReverseSerializer

    def perform_update(self, serializer):
        obj = self.get_object()
        ref_lines = WalletTransactionLine.objects.filter(transaction=obj, ref__isnull=False)
        for ref_line in ref_lines:
            if ref_line.ref.wallet_invoice is not None:
                if self.request.data['is_reversed']:
                    ref_line.ref.wallet_invoice.status = 'REVERSE'
                elif not self.request.data['is_reversed']:
                    ref_line.ref.wallet_invoice.status = 'PAID'
                ref_line.ref.wallet_invoice.save()

        # if isinstance(serializer.ref, RefTransaction) and serializer.is_reversed:
        #     serializer.ref.wallet_invoice.status = 'REVERSE'
        # elif isinstance(serializer.ref, RefTransaction):
        #     serializer.ref.wallet_invoice.status = 'PAID'
        # serializer.ref.wallet_invoice.save()
        serializer.save()


    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     seller_store_name = instance.store.name_fa
    #     client_full_name = f"{instance.client.first_name} {instance.client.last_name}"
    #     amount = instance.amount_rials
    #     created_at = instance.datetime_created

    #     wallet_transaction_id = WalletTransactionLine.objects.filter(ref__wallet_invoice__id=instance.id).first().transaction.id

    #     data = {
    #         'seller_store_name': seller_store_name,
    #         'client_full_name': client_full_name,
    #         'amount': amount,
    #         'created_at': created_at,
    #         'transaction_id': f"GBC00000{wallet_transaction_id}"
    #     }

    #     serializer = self.get_serializer(**data)
    #     return Response(serializer.data)





# from rest_framework import serializers
# from decimal import Decimal
# from datetime import datetime
# class AdditionalSerializer(serializers.ModelSerializer):

#     def number_seprator(number, by=','):
#         if number is None or not str(number).isnumeric():
#             return 0
#         return f'{int(number):{by}}'

#     @staticmethod
#     def translate_number_to_persian(number):
#         if number is None or not str(number).isnumeric():
#             return 0
#         # Fa_to_En= str.maketrans({"۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9"," ":"",})
#         En_to_Fa = str.maketrans(
#             {"0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴", "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
#              " ": "", })
#         return number.translate(En_to_Fa)

#     def datetime_to_jalali(self, d):
#         from persiantools.jdatetime import JalaliDateTime
#         from datetime import timedelta
#         now = JalaliDateTime.to_jalali(d).isoformat()
#         return now

#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         s = {}
#         for field, value in representation.items():
#             s[field] = value
#             print(field, type(value), value)
#             if isinstance(value, (int, float, Decimal)):
#                 s[f'{field}_separate'] = self.number_seprator(value)
#             if isinstance(value, datetime):
#                 s[f'{field}_fa'] = self.datetime_to_jalali(value)
                
#         return s

# class AdditionalNestedCodeForWalletInvoiceSerializer(AdditionalSerializer):
#     # wallet_invoice = WalletInvoiceSerializer()
#     class Meta:
#         model = CodeForWalletInvoice
#         fields = '__all__'


# class WalletTransactionUserBalance(List):
#     def get_queryset(self):
#         keys = ['CBCL', 'CJCL', 'CLCL']
#         grouped = (
#             WalletTransactionLine.objects.filter(
#                 wallet__account__user=self.request.user,
#                 layer__key__in=keys,
#                 layer__isnull=False,
#                 wallet__isnull=False,
#                 currency__isnull=False
#             )
#             .values('layer')  # گروه‌بندی بر اساس layer
#             .annotate(total_amount=Sum('amount'))  # محاسبه مجموع
#         )

#         layers = Layer.objects.filter(key__in=keys)
#         wallet_lines = WalletTransactionLine.objects.filter(
#             wallet__account__user=self.request.user
#         ).select_related('wallet', 'currency')

#         result = []
#         for group in grouped:
#             layer_id = group['layer']
#             total_amount = group['total_amount']
#             layer_obj = layers.get(pk=layer_id)
#             wallet_line = wallet_lines.filter(layer=layer_id).first()
#             if wallet_line:
#                 result.append({
#                     'layer': layer_obj,
#                     'total_amount': total_amount,
#                     'wallet': wallet_line.wallet,
#                     'currency': wallet_line.currency
#                 })
#         return result
#     serializer_class = WalletTransactionLineGroupByLayerSerializer

#     def list(self, request, *args, **kwargs):
#         data = self.get_queryset()
#         serializer = WalletTransactionLineGroupByLayerSerializer(data, many=True)
#         return Response(serializer.data)


class WalletTransactionUserBalance(List):
    serializer_class = WalletTransactionLineGroupByLayerSerializer

    def get_queryset(self):
        keys = ['CBCL', 'CJCL', 'CLCL']

        # Directly construct the ValuesQuerySet
        queryset = (
            WalletTransactionLine.objects
            .filter(
                wallet__account__user=self.request.user,
                layer__key__in=keys,
                layer__isnull=False,
                wallet__isnull=False,
                currency__isnull=False
            )
            .values(
                'layer',
                'wallet',
                'currency'
            )
            .annotate(
                layer_obj=F('layer'),
                total_amount=Sum('amount'),
                wallet_obj=F('wallet'),
                currency_obj=F('currency')
            )
        )
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Prepare the data for serialization
        result = []
        for item in queryset:
            layer = Layer.objects.get(pk=item['layer'])
            result.append({
                'layer': layer,
                'total_amount': item['total_amount'],
                'wallet': item['wallet_obj'],
                'currency': item['currency_obj']
            })

        serializer = WalletTransactionLineGroupByLayerSerializer(result, many=True)
        return Response(serializer.data)
