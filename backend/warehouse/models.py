from django.db import models
from django.utils import timezone
from auth_app.models import Project, Company
from django.contrib.auth.models import User


class WareType(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    icon = models.TextField(blank=True, null=True, default=None)


class Unit(models.Model):
    unit_en = models.CharField(max_length=30, blank=True, null=True, default=None)
    unit_fa = models.CharField(max_length=30, blank=True, null=True, default=None)
    unit_abbreviation = models.CharField(max_length=12, blank=True, null=True, default=None)


class Ware(models.Model):
    name_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    type = models.ForeignKey(WareType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_for_use = models.BooleanField(blank=True, default=False)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, default=None)
    identifier = models.CharField(max_length=20, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True, default=None)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)
    priority = models.IntegerField(blank=True, default=0)
    is_active = models.BooleanField(blank=True, default=True)
    creation_key = models.UUIDField(blank=True, null=True)
    creation_hash = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['project', 'creation_key'], condition=models.Q(creation_key__isnull=False),
            name='warehouse_ware_project_creation_key_unique',
        )]

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(Ware, self).save(*args, **kwargs)


class WarehouseLocation(models.Model):
    name_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    address = models.TextField(blank=True, null=True, default=None)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    owner = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True, default=None)
    projects = models.ManyToManyField(Project)


class WarehouseTransaction(models.Model):
    LEGACY = 'LEGACY'
    RECEIPT = 'RECEIPT'
    OPENING = 'OPENING'
    TRANSFER = 'TRANSFER'
    RETURN = 'RETURN'
    CONSUME = 'CONSUME'
    SCRAP = 'SCRAP'
    MOVEMENT_CHOICES = tuple((value, value) for value in
                             (LEGACY, RECEIPT, OPENING, TRANSFER, RETURN, CONSUME, SCRAP))
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, blank=True, null=True)
    request_key = models.UUIDField(blank=True, null=True)
    payload_hash = models.CharField(max_length=64, blank=True, default='')
    repair_case = models.ForeignKey('visit.RepairCase', on_delete=models.PROTECT,
                                    related_name='material_transactions', null=True, blank=True)
    description = models.TextField(blank=True, null=True, default=None)
    movement_kind = models.CharField(max_length=12, choices=MOVEMENT_CHOICES, default=LEGACY)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['project', 'creator', 'request_key'],
            condition=models.Q(request_key__isnull=False),
            name='warehouse_transfer_user_key_unique',
        )]

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        return super(WarehouseTransaction, self).save(*args, **kwargs)


class TransactionLineType(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    side = models.CharField(max_length=6, blank=True, null=True, default=None)
    involved = models.CharField(max_length=20, blank=True, null=True, default=None)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        return super(TransactionLineType, self).save(*args, **kwargs)


class WarehouseTransactionLine(models.Model):
    ware = models.ForeignKey(Ware, on_delete=models.PROTECT)
    transaction = models.ForeignKey(WarehouseTransaction, on_delete=models.PROTECT, blank=True, default=None)
    amount = models.BigIntegerField(default=0)
    type = models.ForeignKey(TransactionLineType, on_delete=models.PROTECT, blank=True, null=True, default=None)
    location = models.ForeignKey(WarehouseLocation, on_delete=models.PROTECT, blank=True, null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True, default=None)


from visit.models import VisitType, Visit


class WareVisitType(models.Model):
    ware = models.ForeignKey(Ware, on_delete=models.CASCADE)
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, blank=True, null=True, default=None)

class WarehouseLocationPersonnel(models.Model):
    location = models.ForeignKey(WarehouseLocation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        return super().save(*args, **kwargs)


class PartRequest(models.Model):
    """A field worker's request for a spare part during a visit; fulfilment moves stock to the requester."""
    PENDING = 'PENDING'
    FULFILLED = 'FULFILLED'
    REJECTED = 'REJECTED'
    CANCELED = 'CANCELED'
    STATUS_CHOICES = ((PENDING, 'در انتظار'), (FULFILLED, 'تحویل شد'), (REJECTED, 'رد شد'), (CANCELED, 'لغو شد'))
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='part_requests')
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='part_requests')
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name='part_requests')
    ware = models.ForeignKey(Ware, on_delete=models.PROTECT, related_name='part_requests')
    amount = models.PositiveIntegerField()
    note = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    location = models.ForeignKey(WarehouseLocation, on_delete=models.PROTECT, null=True, blank=True)
    stock_transaction = models.ForeignKey(WarehouseTransaction, on_delete=models.PROTECT, null=True, blank=True)
    decision_note = models.CharField(max_length=500, blank=True, default='')
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at', '-id')
