from django.db import models
import uuid
from decimal import Decimal
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.

class Currency(models.Model):
    name_en = models.CharField(max_length=50, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=50, blank=True, null=True, default=None)
    abbreviation = models.CharField(max_length=10, unique=True, help_text="it is key for this table!")


class Layer(models.Model):
    key = models.CharField(max_length=16, unique=True, blank=True, null=True, default=None)
    title = models.CharField(max_length=50)
    verbose_name = models.CharField(max_length=50, blank=True, null=True, default=None)
    priority = models.IntegerField(blank=True, default=0)
    is_active = models.BooleanField(blank=True, default=True)


class WalletType(models.Model):
    name_en = models.CharField(max_length=50, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=50, blank=True, null=True, default=None)
    key = models.CharField(max_length=10, unique=True)
    is_general = models.BooleanField(blank=True, default=False)

class Account(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    signature_identifier = models.UUIDField(blank=True, default=uuid.uuid4, editable=False, unique=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)


    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        return super(Account, self).save(*args, **kwargs)



class Wallet(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    type = models.ForeignKey(WalletType, on_delete=models.CASCADE)
    public_address = models.TextField(max_length=42, editable=False,  blank=True)
    short_address = models.TextField(max_length=16, editable=False, blank=True, null=True, default=None, unique=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            import hashlib
            public_address = hashlib.sha1()
            public_address.update((str(self.account.signature_identifier) + str(self.type.id)).encode())
            self.public_address = public_address.hexdigest().lower()
            self.datetime_created = now
        self.datetime_last_change = now
        return super(Wallet, self).save(*args, **kwargs)


class TransactionType(models.Model):
    key = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=30, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=30, blank=True, null=True, default=None)
    config = models.TextField()
    min_amount = models.BigIntegerField(blank=True, null=True, default=None)
    max_amount = models.BigIntegerField(blank=True, null=True, default=None)
    max_acceptable_rest_amount = models.IntegerField(blank=True, default=0)
    rest_config = models.TextField(null=True, default=None)
    users_hint = models.TextField(blank=True, null=True, default=None)

class AllowedTransactionRule(models.Model):
    from_layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.CASCADE)
    wallet_type = models.ForeignKey(WalletType, on_delete=models.CASCADE, null=True, default=None)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, null=True, default=None)    

class WalletTransaction(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.ForeignKey(TransactionType, on_delete=models.CASCADE, null=True, default=None)
    description = models.CharField(max_length=255, blank=True, null=True, default=None)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)
    is_reversed = models.BooleanField(default=False, blank=True, null=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        return super(WalletTransaction, self).save(*args, **kwargs)


from visit.models import Visit

class WalletInvoice(models.Model):
    class TYPES(models.TextChoices):
        CREDIT = "CREDIT", "CREDIT"
        CASH = "CASH", "CASH"
        POS = "POS", "POS"
        OTHER = "OTHER", "OTHER"


    class STATUS(models.TextChoices):
        PAID = "PAID", 'PAID'
        INITIAL = "INITIAL", 'INITIAL'
        REVERSE = "REVERSE", 'REVERSE'


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_key = models.UUIDField(null=True, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True, default='')
    type = models.CharField(choices=TYPES.choices, max_length=50, blank=True, null=True)
    expert = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='invoice_expert')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, blank=True, null=True, default=None)
    client = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='invoice_client')
    amount_rials = models.BigIntegerField(default=0)
    payable_amount_rials = models.BigIntegerField(blank=True, default=0)
    description = models.TextField(blank=True, null=True, default=None)
    is_closed = models.BooleanField(blank=True, default=False)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)
    status = models.CharField(choices=STATUS.choices, default=STATUS.INITIAL, max_length=18, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['expert', 'request_key'], condition=models.Q(request_key__isnull=False),
            name='invoice_expert_request_key_unique',
        )]

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.datetime_created:
            self.datetime_created = now
            self.payable_amount_rials = int(self.amount_rials)
        self.datetime_last_change = now
        return super(WalletInvoice, self).save(*args, **kwargs)

class CodeForWalletInvoice(models.Model):
    wallet_invoice = models.ForeignKey(WalletInvoice, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=128, blank=True)
    verification_token = models.TextField(blank=True)
    datetime_requested = models.DateTimeField(blank=True, null=True, default=None)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            import secrets
            self.verification_token = secrets.token_hex(32)
            self.datetime_requested = timezone.now()
        return super(CodeForWalletInvoice, self).save(*args, **kwargs)

class RefTransaction(models.Model):
    wallet_invoice = models.ForeignKey(WalletInvoice, on_delete=models.CASCADE, blank=True, null=True, default=None)
    data = models.TextField(blank=True, null=True, default=None)
    
class TransactionLineType(models.Model):
    side = models.CharField(max_length=6, blank=True, null=True, default=None)
    indicator = models.IntegerField(blank=True, default=1)
    affects_on = models.CharField(max_length=255, blank=True, null=True, default=None)
    has_ref = models.BooleanField(blank=True, default=False)
    needs_special_access = models.BooleanField(blank=True, default=False)

class WalletTransactionLine(models.Model):
    transaction = models.ForeignKey(WalletTransaction, on_delete=models.CASCADE)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, blank=True, null=True, default=None)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    type = models.ForeignKey(TransactionLineType, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    ref = models.ForeignKey(RefTransaction, on_delete=models.CASCADE, blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        if self.amount < 0:
            self.side = "FROM"
        elif self.amount > 0:
            self.side = "TO"
        else:
            raise ValueError(_("Amount cannot be zero!"))
        if self.amount * self.type.indicator <= 0:
            raise ValueError(_("Amount sign is invalid for this type!"))
        return super(WalletTransactionLine, self).save(*args, **kwargs)

class VariableConfig(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.BigIntegerField()

