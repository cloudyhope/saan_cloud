from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model

User = get_user_model()

from django.contrib.postgres.indexes import GinIndex, OpClass
# Create your models here.

class SpecificationType(models.Model):
    name = models.CharField(max_length=25)
    verbose_name = models.CharField(max_length=32, blank=True, null=True, default=None)
    category = models.CharField(max_length=25, blank=True, null=True, default=None)
    initial = models.BooleanField(blank=True, default=False)

class Company(models.Model):
    name_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    abbreviation = models.CharField(max_length=255, blank=True, null=True, default=None)
    logo = models.TextField(blank=True, null=True, default=None)

    def delete(self):
        pass


class RequestLog(models.Model):
    endpoint_url = models.CharField(max_length=255, null=True)
    method = models.CharField(max_length=255, null=True)
    user_name = models.CharField(max_length=255, null=True)
    response_code = models.PositiveSmallIntegerField()
    remote_address = models.CharField(max_length=20, null=True)
    device_id = models.CharField(max_length=255, null=True)
    exec_time = models.IntegerField(null=True)
    datetime_created = models.DateTimeField( null=True, blank=True)
    datetime_response_received = models.DateTimeField(null=True, blank=True)
    referer = models.CharField(max_length=255, null=True)
    sent_data = models.CharField(max_length=2056, null=True)

class Country(models.Model):
    name = models.CharField(max_length=35)
    is_active = models.BooleanField(default=False, blank=True)

class Province(models.Model):
    name = models.CharField(max_length=35)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_active = models.BooleanField(default=False, blank=True)

class City(models.Model):
    name = models.CharField(max_length=35)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['province', ]),
        ]

class Config(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField(blank=True, null=True, default=None)
    category = models.CharField(max_length=50, blank=True, null=True, default=None)

    def __str__(self):
        return f"{self.key} | {self.value} | {self.category}" 



class ViewMethod(models.Model):
    view_name = models.CharField(_('view name'), max_length=255)
    method = models.CharField(max_length=10, blank=True, null=True, default=None)
    is_public = models.BooleanField(blank=True, default=False)

    class Meta:
        unique_together = ('view_name', 'method',)
    
    def __str__(self):
        return str(self.id) + ": " + str(self.view_name) + " - " + str(self.method)

class Role(models.Model):
    datetime_created = models.DateTimeField(_('datetime created'), blank=True)
    datetime_last_change = models.DateTimeField(_('datetime last change'), blank=True)
    role_title = models.CharField(_('role title'), max_length=90, unique=True)
    description = models.TextField(_('role description'))
    allowed_view_methods = models.ManyToManyField(ViewMethod, help_text=_('any user with this role has permission to'), blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        super(Role, self).save(*args, **kwargs)

class RoleAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    title = models.CharField(max_length=255, blank=True, null=True, default=None)
    address = models.TextField(null=True, blank=True, default=None)
    postal_code = models.CharField(max_length=16, null=True, blank=True, default=None)
    type = models.ForeignKey(SpecificationType, on_delete=models.CASCADE, related_name='address_type', blank=True, null=True)
    is_deleted = models.BooleanField(blank=True, default=False)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True, default=None)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    datetime_created = models.DateTimeField(null=True, blank=True, default=None)
    datetime_last_change = models.DateTimeField(null=True, blank=True, default=None)


    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        super(Address, self).save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    first_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    last_name = models.CharField(max_length=128, null=True, blank=True, default=None)
    national_code = models.CharField(max_length=10, null=True, blank=True, default=None)
    birth_date = models.DateField(null=True, blank=True, default=None)
    job = models.CharField(max_length=200, null=True, blank=True, default=None)
    sheba = models.CharField(max_length=26, null=True, blank=True, default=None)
    landline_phone = models.CharField(max_length=32, null=True, blank=True, default=None)
    gender = models.BooleanField(blank=True, null=True, default=None)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True, default=None)
    roles = models.ManyToManyField(Role, help_text=_('user roles'), blank=True)
    job_role = models.ForeignKey(SpecificationType, on_delete=models.CASCADE, related_name='job_type', blank=True, null=True)
    skin_type = models.ForeignKey(SpecificationType, on_delete=models.CASCADE, related_name='skin_type', blank=True, null=True)
    hair_type = models.ForeignKey(SpecificationType, on_delete=models.CASCADE, related_name='hair_type', blank=True, null=True)



class PhoneOTP(models.Model):
    code = models.CharField(max_length=5, blank=True)
    phone_number = models.CharField(max_length=15)
    datetime_requested = models.DateTimeField(blank=True)
    verification_token = models.TextField(blank=True)
    wrong_answers_count = models.IntegerField(blank=True, default=0)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_requested = timezone.now()
        self.wrong_answers_count += 1
        super(PhoneOTP, self).save(*args, **kwargs)

