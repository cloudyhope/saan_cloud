from dataclasses import Field
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
# Create your models here.
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


import re


class Company(models.Model):
    name_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    abbreviation = models.CharField(max_length=255, blank=True, null=True, default=None)
    logo = models.TextField(blank=True, null=True, default=None)

    def delete(self):
        pass


class Project(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True, default=None)
    company_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    key = models.CharField(max_length=20, blank=True, null=True, default=None)
    logo = models.TextField(blank=True, null=True, default=None)
    image = models.TextField(blank=True, null=True, default=None)
    primary_color = models.CharField(max_length=20, blank=True, null=True, default=None)
    secondary_color = models.CharField(max_length=20, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    is_active = models.BooleanField(blank=True, default=True)
    promoting_type = models.CharField(max_length=20, blank=True, null=True, default=None)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(Project, self).save(*args, **kwargs)


class Province(models.Model):
    name = models.CharField(max_length=35)


class City(models.Model):
    name = models.CharField(max_length=35)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['province', ]),
        ]


class Region(models.Model):
    name = models.CharField(max_length=35, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=35, blank=True, null=True, default=None)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True, default=None)


class District(models.Model):
    verbose_name = models.CharField(max_length=35, blank=True, null=True, default=None)
    no = models.IntegerField(blank=True, null=True, default=None)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True, default=None)


class ActiveCity(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('city', 'project',)


class FieldValidation(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True, default=None)
    min_value = models.BigIntegerField(blank=True, null=True, default=None)
    max_value = models.BigIntegerField(blank=True, null=True, default=None)
    value_error_msg_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    value_error_msg_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    min_lenght = models.IntegerField(blank=True, null=True, default=None)
    max_lenght = models.IntegerField(blank=True, null=True, default=None)
    lenght_error_msg_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    lenght_error_msg_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_mandatory = models.BooleanField(blank=True, default=False)
    mandatory_error_msg_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    mandatory_error_msg_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    regex = models.CharField(max_length=255, blank=True, null=True, default=None)
    # regex_json = models.JSONField(blank=True, null=True, default=None)
    regex_error_msg_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    regex_error_msg_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    min_choice_count = models.IntegerField(blank=True, null=True, default=None)
    max_choice_count = models.IntegerField(blank=True, null=True, default=None)
    choice_count_error_msg_en = models.CharField(max_length=255, blank=True, null=True, default=None)
    choice_count_error_msg_fa = models.CharField(max_length=255, blank=True, null=True, default=None)


class Role(models.Model):
    ASSET_SCOPES = (
        ('none', 'No asset access'),
        ('client', 'Client buildings'),
        ('assigned', 'Assigned visits'),
        ('supervised', 'Supervised visits'),
        ('project', 'All project assets'),
    )
    title = models.CharField(max_length=25, help_text="Manager, Customer")
    title_abbreviation = models.CharField(max_length=1, help_text="M, C")
    verbose_name = models.CharField(max_length=40, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    priority = models.IntegerField(blank=True, default=0)
    is_active = models.BooleanField(blank=True, default=True)
    asset_scope = models.CharField(max_length=12, choices=ASSET_SCOPES, default='none')


class RoleAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_app_roleassignment')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(blank=True, default=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()


class ExtendedUser(models.Model):
    # gender is Woman if True and Man if False
    MANAGER = 'M'
    CUSTOMER = 'C'
    PROMOTER = 'P'
    # SUPERVISOR = 'V'
    SUPPORT = 'S'
    ROLES = (
        (MANAGER, "Manager"),
        (CUSTOMER, "Customer"),
        (PROMOTER, "Promoter"),
        # (SUPERVISOR, 'Supervisor'),
        (SUPPORT, 'Support'),
    )
    FORM_NOT_COMPLETE = 'F_N_C'
    FORM_COMPLETE = 'F_C'
    READY_TO_ASSIGN = 'R'
    STATUS = (
        (FORM_NOT_COMPLETE, 'Form not completed'),
        (FORM_COMPLETE, 'Form completed'),
        (READY_TO_ASSIGN, 'User is ready to assign'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=80, blank=True, null=True, default=None)
    national_code = models.CharField(max_length=10, blank=True, null=True)
    role = models.CharField(choices=ROLES, max_length=1, default=PROMOTER)
    roles = models.ManyToManyField(Role, help_text=_('user roles'), blank=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, blank=True, null=True, default=None)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True, default=None)
    insurance_number = models.CharField(max_length=255, blank=True, null=True)
    iban = models.CharField(max_length=24, blank=True, null=True)
    birthـcertificateـnumber = models.CharField(max_length=30, blank=True, null=True, verbose_name='شماره شناسنامه')
    birthday = models.DateField(blank=True, null=True, verbose_name='')
    gender = models.BooleanField(blank=True, null=True, default=False)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)
    status = models.CharField(choices=STATUS, max_length=20, default=READY_TO_ASSIGN, blank=True, null=True)
    

    def birth_validator(self):
        this_year = datetime.now().year
        if this_year < self.birthday.year:
            raise ValidationError('Not born yet!')
        elif (this_year - self.birthday.year) < 18:
            raise ValidationError('Not 18 years old or older!')
        else:
            return self.birthday

    def iban_validator(self):
        if self.iban.find('IR') == -1:
            self.iban = 'IR' + self.iban
        if self.iban.find('-') != -1:
            self.iban = self.iban.replace('-', '')
        value = str(self.iban)
        value = value[3:] + value[:3]
        value = value.replace('IR', '1828')
        value = value.int(value)
        if not (value % 97 == 1):
            raise ValidationError('Invalid IBN algorithm')

        return self.iban

    def national_validator(self):
        if not re.search(r'^\d{10}$', self.national_code): return ValidationError('Not a valid National Algorithm')
        check = int(self.national_code[9])
        s = sum(int(self.national_code[x]) * (10 - x) for x in range(9)) % 11
        if check == s if s < 2 else check + s == 11:
            return self.national_code
        return ValidationError('Not a valid National Algorithm')

    def save(self, *args, **kwargs):
        if self.iban:
            self.iban = self.iban_validator()
        if self.national_code:
            self.national_code = self.national_validator()
        if self.birthday:
            self.birthday = self.birth_validator()
        super(ExtendedUser, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        return super(ExtendedUser, self).save(*args, **kwargs)


class Document(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    abbreviation = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    is_mandatory = models.BooleanField(default=False)

    def delete(self):
        pass


class DocumentPhoto(models.Model):
    NOT_CHECKED = 'NOT_CHECKED'
    CONFIRMED = 'CONFIRMED'
    REJECTED = 'REJECTED'
    CONFIRMATION_CHOICES = (
        (NOT_CHECKED, 'NOT_CHECKED'),
        (CONFIRMED, 'CONFIRMED'),
        (REJECTED, 'REJECTED'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, blank=True, null=True, default=None)
    file = models.TextField(blank=True, null=True, default=None)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)
    supervisor_confirm = models.CharField(max_length=12, blank=True, choices=CONFIRMATION_CHOICES,
                                          default='NOT_CHECKED')
    is_deleted = models.BooleanField(default=False, blank=True)
    is_checked = models.BooleanField(default=False, blank=True)
    confirm_status = models.CharField(max_length=12, blank=True, choices=CONFIRMATION_CHOICES,
                                      default='NOT_CHECKED')

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return super(DocumentPhoto, self).save(*args, **kwargs)


class OTP(models.Model):
    phone_number = models.CharField(max_length=16)
    otp = models.CharField(max_length=128, blank=True)
    verification_token = models.TextField(blank=True)
    datetime_requested = models.DateTimeField(blank=True, null=True, default=None)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_requested = timezone.now()
        super(OTP, self).save(*args, **kwargs)


class SupervisorChangeLog(models.Model):
    supervisor_record = models.ForeignKey('Supervisor', on_delete=models.CASCADE)
    created = models.BooleanField(blank=True, default=False)
    is_active_set_to = models.BooleanField(blank=True, default=False)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.phone_verified = False
            self.datetime_created = now
        self.datetime_last_change = now
        return super(SupervisorChangeLog, self).save(*args, **kwargs)


class Supervisor(models.Model):
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Supervisor_Supervisor')
    promoter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Supervisor_Promoter')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_active = models.BooleanField(blank=True, default=True)

    class Meta:
        unique_together = (
            'supervisor',
            'promoter',
            'project',
        )

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        log = SupervisorChangeLog()
        now = timezone.now()
        if not self.id:
            self.phone_verified = False
            self.datetime_created = now
            log.created = True
        log.is_active_set_to = self.is_active
        log.supervisor_record = self
        self.datetime_last_change = now
        return_val = super(Supervisor, self).save(*args, **kwargs)
        log.save()
        return return_val

    def delete(self, *args, **kwargs):
        self.is_active = False
        return self.save()


class AdminMenu(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    parent = models.ForeignKey('AdminMenu', on_delete=models.CASCADE, related_name='parent_menu', null=True, blank=True,
                               default=None)
    has_submenu = models.BooleanField(blank=True, default=False)
    priority = models.IntegerField()
    name = models.CharField(max_length=40, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=60, blank=True, null=True, default=None)
    active_icon = models.TextField(blank=True, null=True, default=None)
    deactive_icon = models.TextField(blank=True, null=True, default=None)
    has_iframe = models.BooleanField(blank=True, default=False)
    iframe_link = models.TextField(blank=True, null=True, default=None)
    frontend_route_name = models.CharField(max_length=80, blank=True, null=True, default=None)
    frontend_route_url = models.CharField(max_length=255, blank=True, null=True, default=None)
    frontend_api_queryparams = models.CharField(max_length=255, blank=True, null=True, default=None)
    frontend_route_params = models.JSONField(blank=True, null=True, default=None)
    is_active = models.BooleanField(blank=True, default=True)


from visit.models import AnswerType, Question
from survey.models import SurveyQuestion


class QuestionAnswerTypeValidation(models.Model):
    VISITAPP = 'V'
    SURVEYAPP = 'S'
    IS_FOR = (
        (VISITAPP, "For Visit App"),
        (SURVEYAPP, "For Survey App"),
    )
    is_for = models.CharField(max_length=1, blank=True, default='V', choices=IS_FOR)
    visit_question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=True, null=True, default=None)
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, blank=True, null=True, default=None)
    validation = models.ForeignKey(FieldValidation, on_delete=models.CASCADE, blank=True, null=True, default=None)
    answer_type = models.ForeignKey(AnswerType, on_delete=models.CASCADE)


class UploadedFile(models.Model):
    EDUCATION = 'EDU'
    ETC = "ETC"
    TYPE_CHOICES = (
        (EDUCATION, "Education"),
        (ETC, "Etc."),
    )
    file = models.TextField(blank=True, null=True, default=None)
    name = models.CharField(max_length=40, blank=True, null=True, default=None)
    type = models.CharField(max_length=3, blank=True, null=True, default=None, choices=TYPE_CHOICES)
    description = models.TextField(blank=True, null=True, default=None)
    icon = models.TextField(blank=True, null=True, default=None)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_deleted = models.BooleanField(blank=True, default=False)
    priority = models.IntegerField(blank=True, default=0)


class AuthenticationImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    image = models.TextField(blank=True)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        super(AuthenticationImage, self).save(*args, **kwargs)

from survey.models import SurveyFillOut
from visit.models import Visit
from config.models import Config
class AuthenticationValidationLog(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    survey_fillout = models.ForeignKey(SurveyFillOut, on_delete=models.CASCADE, blank=True, null=True, default=None)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, blank=True, null=True, default=None)
    national_id = models.CharField(max_length=12, blank=True, null=True, default=None)
    phone_number = models.CharField(max_length=20, blank=True, null=True, default=None)
    sheba_number = models.CharField(max_length=50, blank=True, null=True, default=None)
    sheba_message = models.TextField(blank=True, null=True, default=None)
    phone_message = models.TextField(blank=True, null=True, default=None)
    birth_date = models.CharField(max_length=50, blank=True, null=True, default=None)
    message = models.ForeignKey(Config, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_sheba_valid = models.BooleanField(blank=True, default=False)
    is_phone_valid = models.BooleanField(blank=True, default=False)
    is_valid = models.BooleanField(blank=True, default=False)
    is_new = models.BooleanField(blank=True, default=False)
    is_main = models.BooleanField(blank=True, default=False)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)

from django.utils.translation import gettext_lazy as _


class ViewMethod(models.Model):
    GET = 'GET'
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    METHOD_CHOICES = (
        (GET, "GET"),
        (POST, "POST"),
        (PUT, "PUT"),
        (DELETE, "DELETE"),
        (OPTIONS, "OPTIONS"),
        (PATCH, "PATCH"),
    )
    view_name = models.CharField(_('view name'), max_length=255, blank=False, null=False)
    method = models.CharField(_('method name'), max_length=10, blank=True, null=True, default=None,
                              choices=METHOD_CHOICES)

    def __str__(self):
        return str(self.id) + ": " + str(self.view_name) + '_' + str(self.method)


class RoleView(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    view_method_name = models.ForeignKey(ViewMethod, on_delete=models.CASCADE)
    can_create = models.BooleanField(blank=True, default=False)
    can_update = models.BooleanField(blank=True, default=False)
    can_delete = models.BooleanField(blank=True, default=False)
    can_view = models.BooleanField(blank=True, default=False)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)


class ModelField(models.Model):
    model_name = models.CharField(max_length=255, blank=False, null=False)
    field_name = models.CharField(max_length=255, blank=False, null=False)
    field_type = models.CharField(max_length=255, blank=False, null=False)


class RoleViewModelField(models.Model):
    role_view = models.ForeignKey(RoleView, on_delete=models.CASCADE)
    model_field = models.ForeignKey(ModelField, on_delete=models.CASCADE)
    can_update = models.BooleanField(blank=True, default=False)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)


class Limiter(models.Model):
    key = models.CharField(max_length=255, blank=True, null=True, default=None)
    value = models.CharField(max_length=255, blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)


class RoleViewLimiter(models.Model):
    role_view = models.ForeignKey(RoleView, on_delete=models.CASCADE)
    limiter = models.ForeignKey(Limiter, on_delete=models.CASCADE)
    is_active = models.BooleanField(blank=True, default=False)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)


class LogLimiter(models.Model):
    key = models.CharField(max_length=255, blank=True, null=True, default=None)
    value = models.CharField(max_length=255, blank=True, null=True, default=None)
    model = models.CharField(max_length=255, blank=True, null=True, default=None)
    view_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_get = models.BooleanField(blank=True, default=False)
    is_put = models.BooleanField(blank=True, default=False)
    is_patch = models.BooleanField(blank=True, default=False)
    is_options = models.BooleanField(blank=True, default=False)
    is_delete = models.BooleanField(blank=True, default=False)
    is_post = models.BooleanField(blank=True, default=False)
    is_solved = models.BooleanField(blank=True, default=False)
    user = models.CharField(max_length=255, blank=True, null=True, default=None)
    project = models.CharField(max_length=255, blank=True, null=True, default=None)
    role_view_limiter = models.ForeignKey(RoleViewLimiter, on_delete=models.CASCADE)
    datetime_last_change = models.DateTimeField(auto_now=True, blank=True, null=True)
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
