from rest_framework import serializers

from core.modules.serializers import AdditionalSerializer
from wallet.models import (
    Currency,
    Layer,
    WalletType,
    Account,
    Wallet,
    WalletTransaction,
    TransactionType,
    AllowedTransactionRule,
    RefTransaction,
    TransactionLineType,
    WalletTransactionLine,
    WalletInvoice,
    CodeForWalletInvoice,
)

# from wallet.serializers import (

# )
from auth_app.serializers import (
    ExtendedUserSerializer,
    LiteExtendedUserSerializer,
    LiteUserSerializer,
)

from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
import uuid
from decimal import Decimal
from django.utils import timezone


# Create your models here.

class CurrencySerializer(AdditionalSerializer):
    class Meta:
        model = Currency
        fields = '__all__'


class LayerSerializer(AdditionalSerializer):
    class Meta:
        model = Layer
        fields = '__all__'


class WalletTypeSerializer(AdditionalSerializer):
    class Meta:
        model = WalletType
        fields = '__all__'


class AccountSerializer(AdditionalSerializer):
    user = LiteUserSerializer()

    class Meta:
        model = Account
        fields = '__all__'


class OnlyAccountSerializer(AdditionalSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class WalletSerializer(AdditionalSerializer):
    account = AccountSerializer()
    type = WalletTypeSerializer()

    class Meta:
        model = Wallet
        fields = '__all__'

class WalletOneLevelSerializer(AdditionalSerializer):

    class Meta:
        model = Wallet
        fields = '__all__'


class OnlyWalletSerializer(AdditionalSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'


class TransactionTypeSerializer(AdditionalSerializer):
    class Meta:
        model = TransactionType
        fields = '__all__'


class AllowedTransactionRuleSerializer(AdditionalSerializer):
    from_layer = LayerSerializer()
    transaction_type = TransactionTypeSerializer()
    wallet_type = WalletTypeSerializer()

    class Meta:
        model = AllowedTransactionRule
        fields = '__all__'


class OnlyAllowedTransactionRuleSerializer(AdditionalSerializer):
    class Meta:
        model = AllowedTransactionRule
        fields = '__all__'


class WalletTransactionSerializer(AdditionalSerializer):
    transaction_id = serializers.SerializerMethodField()
    creator = ExtendedUserSerializer()

    def format_integer(self, num):
        return f"{num:08}"

    def get_transaction_id(self, obj):
        return "SN-" + self.format_integer(obj.id)

    class Meta:
        model = WalletTransaction
        fields = '__all__'


class OnlyWalletTransactionSerializer(AdditionalSerializer):
    class Meta:
        model = WalletTransaction
        fields = '__all__'


class WalletTransactionToggleReverseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ('is_reversed',)


class RefTransactionSerializer(AdditionalSerializer):
    class Meta:
        model = RefTransaction
        fields = '__all__'


class WalletTransactionLineTypeSerializer(AdditionalSerializer):
    class Meta:
        model = TransactionLineType
        fields = '__all__'


class WalletTransactionLineSerializer(AdditionalSerializer):
    transaction = WalletTransactionSerializer()
    wallet = WalletSerializer()
    layer = LayerSerializer()
    currency = CurrencySerializer()

    class Meta:
        model = WalletTransactionLine
        fields = '__all__'


class OnlyWalletTransactionLineSerializer(AdditionalSerializer):
    class Meta:
        model = WalletTransactionLine
        fields = '__all__'


#####################################
# Custom serializers:
#####################################

class BalancesSerializer(serializers.Serializer):
    currency = CurrencySerializer()
    layer = LayerSerializer()
    balance = serializers.IntegerField()


class WalletWithBalanceSerializer(AdditionalSerializer):
    account = AccountSerializer()
    type = WalletTypeSerializer()
    balances = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = (
            "account",
            "type",
            "public_address",
            "short_address",
            "datetime_created",
            "datetime_last_change",
            "balances",
        )

    def get_balances(self, obj):
        from django.db.models import Sum
        result = []
        currencies = Currency.objects.all()
        layers = Layer.objects.filter(is_active=True)
        base_query = WalletTransactionLine.objects.filter(wallet=obj, transaction__is_reversed=False)
        for currency in currencies:
            for layer in layers:
                balance = base_query.filter(currency=currency, layer=layer).aggregate(Sum('amount'))['amount__sum']
                # if balance is None:
                #     continue
                result.append(
                    {
                        "currency": currency,
                        "layer": layer,
                        "balance": balance
                    }
                )
        return BalancesSerializer(result, many=True).data


class WalletGetSignatureSerializer(AdditionalSerializer):
    signature = serializers.SerializerMethodField()
    encryption_key_n = serializers.SerializerMethodField()
    encryption_key_e = serializers.SerializerMethodField()
    wallets = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = (
            'user',
            'signature',
            'encryption_key_n',
            'encryption_key_e',
            'wallets',
        )

    def get_wallets(self, obj):
        return WalletWithBalanceSerializer(Wallet.objects.filter(account=obj), many=True).data

    def get_signature(self, obj):
        from wallet.secrets import WalletCrypt
        crypt = WalletCrypt()
        return crypt.generate_signature(obj.signature_identifier)

    def get_encryption_key_n(self, obj):
        from wallet.secrets import WalletCrypt
        return WalletCrypt.public_numbers()[0]

    def get_encryption_key_e(self, obj):
        from wallet.secrets import WalletCrypt
        return WalletCrypt.public_numbers()[1]


class WalletBalanceEntrySerializer(serializers.ModelSerializer):
    type = WalletTypeSerializer()
    balances = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ('type', 'balances')

    def get_balances(self, obj):
        return WalletWithBalanceSerializer().get_balances(obj)


class WalletBalanceSerializer(serializers.ModelSerializer):
    user = LiteUserSerializer()
    wallets = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('user', 'wallets')

    def get_wallets(self, obj):
        return WalletBalanceEntrySerializer(Wallet.objects.filter(account=obj), many=True).data


class WalletPlaceTransactionSerializer(serializers.Serializer):
    signature = serializers.CharField()
    data = serializers.CharField()


class CreateWalletForUserSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    wallet_type_key = serializers.CharField(required=True)
    short_address = serializers.CharField(allow_null=True)


class OnlyWalletInvoiceSerializer(AdditionalSerializer):
    class Meta:
        model = WalletInvoice
        exclude = ('request_key', 'payload_hash')


class WalletInvoiceSerializer(AdditionalSerializer):
    expert = LiteUserSerializer()
    client = LiteUserSerializer()


    class Meta:
        model = WalletInvoice
        exclude = ('request_key', 'payload_hash')


class OnlyWalletInvoiceSerializer(AdditionalSerializer):
    class Meta:
        model = WalletInvoice
        exclude = ('request_key', 'payload_hash')


class CreateWalletInvoiceSerializer(AdditionalSerializer):
    request_key = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = WalletInvoice
        fields = ('id', 'visit', 'amount_rials', 'description', 'type', 'request_key')
        read_only_fields = ('id',)
        extra_kwargs = {'type': {'required': True, 'allow_null': False, 'allow_blank': False}}

    def validate_amount_rials(self, value):
        if value <= 0 or value > 1_000_000_000_000:
            raise serializers.ValidationError('مبلغ باید مثبت و در محدوده مجاز باشد.')
        return value


class NestedCodeForWalletInvoiceSerializer(AdditionalSerializer):
    wallet_invoice = WalletInvoiceSerializer()

    class Meta:
        model = CodeForWalletInvoice
        fields = ('id', 'wallet_invoice', 'datetime_requested')


class InvoiceCodeRequestSerializer(serializers.Serializer):
    wallet_invoice = serializers.UUIDField()


class InvoiceCodeValidateSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    wallet_invoice = serializers.UUIDField()
    verification_token = serializers.CharField(max_length=128)
    code = serializers.RegexField(r'^\d{5}$')

class WalletInvoiceReceiptSerializer(serializers.ModelSerializer):
    expert = LiteUserSerializer()
    client = LiteUserSerializer()
    transaction = serializers.SerializerMethodField()

    class Meta:
        model = WalletInvoice
        fields = (
            'id',
            'type',
            'expert',
            # 'store',
            # 'store_loyalty_plan',
            'client',
            'amount_rials',
            'payable_amount_rials',
            'description',
            'is_closed',
            'datetime_created',
            'datetime_last_change',
            'transaction',
        )

    def get_transaction(self, obj):
        wallet_transaction_line = WalletTransactionLine.objects.filter(ref__wallet_invoice__id=obj.id).first()
        if wallet_transaction_line is None:
            return None
        else:
            return WalletTransactionSerializer(wallet_transaction_line.transaction, many=False).data


class StoreWalletInvoiceSerializer(AdditionalSerializer):
    client = LiteUserSerializer()

    class Meta:
        model = WalletInvoice
        exclude = ('request_key', 'payload_hash')



class WalletTransactionLineGroupByLayerSerializer(serializers.Serializer):
    layer = LayerSerializer()
    total_amount = serializers.IntegerField()
    wallet = WalletOneLevelSerializer()
    currency = CurrencySerializer()

    class Meta:
        fields = ['layer', 'total_amount', 'wallet', 'currency']

class ChargeWalletByUsernameSerializer(serializers.Serializer):
    username = serializers.CharField()
    amount = serializers.IntegerField()
