from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid
from auth_app.models import *
# Create your models here.

class MoreInfoKey(models.Model):
    key = models.CharField(max_length=50)


class StoreCategory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    verbose_name = models.CharField(max_length=100)


class Store(models.Model):
    """Stores managed independently from building/elevator visits."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(StoreCategory, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=25)
    customer_code = models.CharField(max_length=25, blank=True, default='')
    phone = models.CharField(max_length=16, blank=True, default='')
    mobile_phone = models.CharField(max_length=16, blank=True, default='')
    owner_name = models.CharField(max_length=255, blank=True, default='')
    owner_national_code = models.CharField(max_length=10, blank=True, default='')
    address = models.TextField(blank=True, default='')
    postal_code = models.CharField(max_length=10, blank=True, default='')
    latitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    period = models.PositiveIntegerField(default=1)
    visit_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_visiting = models.BooleanField(default=False)
    datetime_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['project', 'code'], name='store_project_code_unique')]

class MoreInfo(models.Model):
    key = models.ForeignKey(MoreInfoKey, on_delete=models.CASCADE)
    value = models.CharField(max_length=255, null=True, default=None)

class AnswerType(models.Model):
    name = models.CharField(max_length=30)
    field = models.CharField(max_length=30)
    priority = models.BigIntegerField(default=1)


class AnswerChoice(models.Model):
    question = models.ForeignKey('Question', related_name="related_question", on_delete=models.CASCADE, blank=True, null=True, default=None)
    answer = models.CharField(max_length=100)
    score = models.IntegerField(blank=True, null=True, default=None)

from survey.models import Survey
from config.models import AddIn
class VisitType(models.Model):
    title = models.CharField(max_length=40, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=40, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    has_supervision = models.BooleanField(blank=True, default=False)
    is_active = models.BooleanField(blank=True, default=True)
    default_wage = models.BigIntegerField(blank=True, default=0)
    # The field worker must enter the code shown in the client app to finish this kind of service.
    requires_client_code = models.BooleanField(blank=True, default=False)
    # Show the service fee (total_wage) in the client's report; off by default because it is also the worker's pay.
    show_wage_in_report = models.BooleanField(blank=True, default=False)
    # 1 (routine) to 5 (specialist work); compared with the worker's grade when assigning.
    complexity = models.PositiveSmallIntegerField(blank=True, default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True, default=None)
    surveys = models.ManyToManyField(Survey)
    add_ins = models.ManyToManyField(AddIn)



class ReportCategory(models.Model):
    name = models.CharField(max_length=30)
    verbose_name = models.CharField(max_length=30)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_for_supervision = models.BooleanField(blank=True, default=False)

class QuestionType(models.Model):
    name = models.CharField(max_length=30)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=40, default="")
    is_mandatory = models.BooleanField(blank=True, default=False)
    report_category = models.ForeignKey(
        ReportCategory, on_delete=models.CASCADE, blank=True, null=True, default=None)
    description = models.TextField(default="")
    is_for_supervision = models.BooleanField(blank=True, default=False)
    is_active = models.BooleanField(blank=True, default=True)


class Question(models.Model):
    TGENERAL = 'GE'
    TSHELF = 'SH'
    TSALE = 'SA'
    TVIOLATION = 'V'
    TFACTOR = 'FA'
    QUESTIONS_CHOICES = (
        (TGENERAL, 'General'),
        (TSHELF, 'Shelf'),
        (TSALE, 'Sale'),
        (TVIOLATION, 'V'),
        (TFACTOR, 'FA'),

    )
    ABOOL = 'YN'
    AMULTICHOICE = 'MC'
    ASCORE = 'SC'
    ADESC = 'DE'
    ANUMBER = 'NO'
    APRICE = 'PR'
    ANSWER_TYPE_CHOICES = (
        (ABOOL, 'Yes/No'),
        (AMULTICHOICE, 'MultiChoices'),
        (ASCORE, 'Score'),
        (ADESC, 'Description'),
        (ANUMBER, 'Number'),
        (APRICE, 'Price'),
    )
    type = models.CharField(max_length=2, choices=QUESTIONS_CHOICES)
    question_type = models.ForeignKey(
        QuestionType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    text = models.TextField()
    short_text = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    answer_type = models.ManyToManyField(AnswerType)
    has_bool_expected_value = models.BooleanField(blank=True, default=False)
    bool_unexpected_value = models.BooleanField(
        blank=True, null=True, default=None)
    # othertype_expected_value = models.BooleanField(blank=True, null=True, default=None)
    # othertype_expected_value = models.BooleanField(blank=True, null=True, default=None)
    # othertype_expected_value = models.BooleanField(blank=True, null=True, default=None)
    score = models.IntegerField(blank=True, null=True, default=None)
    priority = models.IntegerField(blank=True, null=True, default=None)
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, null=True, blank=True, default=None)
    answer_choices = models.ManyToManyField(
        AnswerChoice, related_name='Valid_Answers')
    dropdown_choices = models.ManyToManyField(AnswerChoice, related_name='dropdown_choices')
    radio_choices = models.ManyToManyField(AnswerChoice, related_name='radio_choices')
    customer_category = models.CharField(
        max_length=30, default=None, blank=True, null=True)
    is_mandatory = models.BooleanField(blank=True, default=False)
    is_active = models.BooleanField(default=True, blank=True)
    report_category = models.ForeignKey(
        ReportCategory, on_delete=models.CASCADE, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    is_for_decision = models.BooleanField(blank=True, default=False)
    decision_rank = models.IntegerField(blank=True, null=True, default=None)



class Visit(models.Model):
    NOTVISITED = '0'
    INPROGRESS = '1'
    COMPLETED = '2'
    APPROVED = '3'
    REJECTED = '4'
    RETRY = '5'
    SUSPEND = '6'
    STATUS_CHOICES = (
        (NOTVISITED, '0'),
        (INPROGRESS, '1'),
        (COMPLETED, '2'),
        (APPROVED, '3'),
        (REJECTED, '4'),
        (RETRY, '5'),
        (SUSPEND, '6'),
    )
    type = models.ForeignKey(VisitType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='creator')
    expert = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='expert', null=True, default=None, blank=True)
    promoter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='promoter', null=True, default=None, blank=True)
    building = models.ForeignKey('Building', on_delete=models.CASCADE, blank=True, null=True, default=None)
    elevator = models.ManyToManyField('Elevator', related_name='visit_elevator', blank=True)
    visit_turn = models.IntegerField(blank=True, null=True, default=None)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    is_deleted = models.BooleanField(blank=True, default=False)
    checked_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='checker', null=True, default=None, blank=True)
    rejection_reason = models.TextField(default=None, null=True, blank=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)
    start_datetime = models.DateTimeField(blank=True, null=True, default=None)
    visit_comment = models.TextField(null=True, default=None)
    is_last_day = models.BooleanField(blank=True, default=False)
    comment_publisher = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, default=None, blank=True)
    prevented_by_score = models.BooleanField(blank=True, default=False)
    is_active = models.BooleanField(blank=True, default=False)
    is_deleted = models.BooleanField(blank=True, default=False)
    has_due_date = models.BooleanField(blank=True, default=False)
    due_date = models.DateField(blank=True, null=True, default=None)
    total_wage = models.BigIntegerField(blank=True, null=True, default=None)
    supervision_status = models.CharField(max_length=1, choices=STATUS_CHOICES, blank=True, default='0')
    # Six-digit code shown to the building's client users; created on first need (visit.field_ops).
    completion_code = models.CharField(max_length=6, blank=True, default='')
    completion_code_failures = models.PositiveSmallIntegerField(default=0)
    completion_code_locked_until = models.DateTimeField(null=True, blank=True)
    maintenance_plan = models.ForeignKey('MaintenancePlan', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='visits')


    # class Meta:
    #     unique_together = ('building', 'visit_turn', 'is_deleted',)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            # if self.elevator is not None:
            #     self.building = BuildingElevator.objects.filter(elevator=self.elevator).first().building
            self.datetime_created = timezone.now()
            try:
                self.total_wage = self.type.default_wage
            except:
                pass
        self.datetime_last_change = timezone.now()
        super(Visit, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()


class VisitReportSnapshot(models.Model):
    """Immutable client-facing answer content captured when a visit completes."""
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='report_snapshots')
    version = models.PositiveIntegerField(default=1)
    payload = models.JSONField()
    checksum = models.CharField(max_length=64)
    source = models.CharField(max_length=30, default='completion')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['visit', 'version'], name='visit_report_snapshot_version_unique')]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('Report snapshots are immutable.')
        return super().save(*args, **kwargs)


class ClientVisitFeedback(models.Model):
    """A client's personal acknowledgement and service rating."""
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='client_feedback')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    note = models.CharField(max_length=1000, blank=True, default='')
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['visit', 'user'], name='client_visit_feedback_user_unique')]



class Client(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True)
    CUSTOMER = "Customer"
    BUSINESS = "Business"
    TYPES = (
        (CUSTOMER, "Customer"),
        (BUSINESS, "Business"),
    )
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    avatar_photo = models.TextField(blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    legacy_visits = models.ManyToManyField(Visit, blank=True, related_name='legacy_client_links')
    visit_types = models.ManyToManyField(VisitType, blank=True, related_name='clients')
    type = models.CharField(max_length=10, choices=TYPES, default="Customer")
    # Denormalised priority score (0-100) maintained by visit.priority; null when no factor applies.
    priority_score = models.FloatField(null=True, blank=True, db_index=True)


class ServiceRequestSubmission(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    creator = models.ForeignKey(User, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    payload_hash = models.CharField(max_length=64)
    visits = models.ManyToManyField(Visit, related_name='service_submissions')
    datetime_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['project', 'creator', 'request_key'], name='service_request_user_key_unique',
        )]

class UserClient(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class ProductModel(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    model_number = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    model_number = models.CharField(max_length=20, blank=True, null=True, default=None)
    type = models.CharField(max_length=25, blank=True, null=True, default=None)

class Product(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True)
    model = models.ForeignKey(ProductModel, on_delete=models.CASCADE, blank=True, null=True, default=None)
    serial_number = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_used = models.BooleanField(blank=True, default=False)
    status = models.CharField(max_length=25, blank=True, null=True, default=None)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super().save(*args, **kwargs)

class Elevator(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True)

    ELEVATOR_TYPE_CHOICES = [
        ("TRACTION", "TRACTION"),
        ("HYDRAULIC", "HYDRAULIC"),
    ]
    USAGE_TYPE_CHOICES = [
        ("RESIDENTIAL", "RESIDENTIAL"),
        ("OFFICE", "OFFICE"),
        ("COMMERCIAL", "COMMERCIAL"),
        ("INDUSTRIAL", "INDUSTRIAL"),
    ]
    OPERATION_TYPE_CHOICES = [
        ("SIMPLEX", "SIMPLEX"),
        ("DUPLEX", "DUPLEX"),
        ("GROUP", "GROUP"),
    ]
    MOTOR_TYPE_CHOICES = [
        ("GEARED", "GEARED"),
        ("GEARLESS", "GEARLESS"),
    ]
    MOTOR_ENCODER_TYPE_CHOICES = [
        ("1024_24V", "1024_24V"),
        ("1024_5V", "1024_5V"),
        ("ERN_1387", "ERN_1387"),
        ("ERN_1313", "ERN_1313"),
        ("ERN_413", "ERN_413"),
        ("OTHER", "OTHER"),
    ]
    CONTROL_PANEL_TYPE_CHOICES = [
        ("MR", "MR"),
        ("MRL", "MRL"),
    ]
    DOOR1_TYPE_CHOICES = [
        ("SWING", "SWING"),
        ("SEMI_AUTO", "SEMI_AUTO"),
        ("AUTO", "AUTO"),
    ]
    DOOR2_TYPE_CHOICES = [
        ("SWING", "SWING"),
        ("SEMI_AUTO", "SEMI_AUTO"),
        ("AUTO", "AUTO"),
    ]
    DOOR3_TYPE_CHOICES = [
        ("SWING", "SWING"),
        ("SEMI_AUTO", "SEMI_AUTO"),
        ("AUTO", "AUTO"),
    ]
    CONTROL_SYSTEM_TYPE_CHOICES = [
        ("OPEN_LOOP", "OPEN_LOOP"),
        ("CLOSED_LOOP", "CLOSED_LOOP"),
    ]
    EMERGENCY_SYSTEM_TYPE_CHOICES = [
        ("NONE", "NONE"),
        ("UPS", "UPS"),
        ("HDRU", "HDRU"),
    ]
    INPUT_VOLTAGE_CHOICES = [
        ("SINGLE_PHASE", "SINGLE_PHASE"),
        ("THREE_PHASE", "THREE_PHASE"),
        ("OTHER", "OTHER"),
    ]
    WEIGHT_SENSOR_CHOICES = [
        ("NONE", "NONE"),
        ("EXISTS", "EXISTS"),
    ]
    FIREFIGHTER_MODE_CHOICES = [
        ("INACTIVE", "INACTIVE"),
        ("MODE1", "MODE1"),
        ("MODE2", "MODE2"),
    ]
    STANDARD_TYPE_CHOICES = [
        ("EN81", "EN81"),
        ("EN81-20", "EN81-20"),
    ]
    LANDING_CALL_COMM_TYPE_CHOICES = [
        ("SERIAL", "SERIAL"),
        ("PARALLEL", "PARALLEL"),
    ]



    title = models.CharField(max_length=255, blank=True, null=True, default=None)
    type = models.CharField(max_length=25, blank=True, null=True, default=None)
    capacity = models.CharField(max_length=10, blank=True, null=True, default=None)
    number_of_floors = models.IntegerField(blank=True, default=1)

    elevator_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=ELEVATOR_TYPE_CHOICES)
    usage_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=USAGE_TYPE_CHOICES)
    cabin_capacity_kg = models.IntegerField(blank=True, null=True, default=None)
    stops_count = models.IntegerField(blank=True, null=True, default=None)
    operation_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=OPERATION_TYPE_CHOICES)
    motor_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=MOTOR_TYPE_CHOICES)
    motor_brand = models.CharField(max_length=25, blank=True, null=True, default=None)
    motor_power_kw = models.IntegerField(blank=True, null=True, default=None)
    motor_nameplate_image = models.TextField(max_length=25, blank=True, null=True, default=None)
    motor_encoder_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=MOTOR_ENCODER_TYPE_CHOICES)
    elevator_speed_mps = models.IntegerField(blank=True, null=True, default=None)
    control_panel_brand = models.CharField(max_length=25, blank=True, null=True, default=None)
    control_panel_serial = models.CharField(max_length=25, blank=True, null=True, default=None)
    control_panel_image = models.TextField(max_length=25, blank=True, null=True, default=None)
    control_panel_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=CONTROL_PANEL_TYPE_CHOICES)
    door_brand = models.CharField(max_length=25, blank=True, null=True, default=None)
    door_count = models.IntegerField(blank=True, null=True, default=None)
    door1_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=DOOR1_TYPE_CHOICES)
    door1_voltage = models.CharField(max_length=25, blank=True, null=True, default=None)
    door2_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=DOOR2_TYPE_CHOICES)
    door2_voltage = models.CharField(max_length=25, blank=True, null=True, default=None)
    door3_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=DOOR3_TYPE_CHOICES)
    door3_voltage = models.CharField(max_length=25, blank=True, null=True, default=None)
    inverter_type = models.CharField(max_length=25, blank=True, null=True, default=None)
    inverter_power = models.CharField(max_length=25, blank=True, null=True, default=None)
    control_system_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=CONTROL_SYSTEM_TYPE_CHOICES)
    emergency_system_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=EMERGENCY_SYSTEM_TYPE_CHOICES)
    input_voltage = models.CharField(max_length=25, blank=True, null=True, default=None, choices=INPUT_VOLTAGE_CHOICES)
    weight_sensor = models.CharField(max_length=25, blank=True, null=True, default=None, choices=WEIGHT_SENSOR_CHOICES)
    firefighter_mode = models.CharField(max_length=25, blank=True, null=True, default=None, choices=FIREFIGHTER_MODE_CHOICES)
    standard_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=STANDARD_TYPE_CHOICES)
    landing_call_comm_type = models.CharField(max_length=25, blank=True, null=True, default=None, choices=LANDING_CALL_COMM_TYPE_CHOICES)
    priority_score = models.FloatField(null=True, blank=True, db_index=True)


# for key in d.keys():
#     print(key + " = " + "models." + ("TextField" if "format" in d[key].keys() else "CharField" if d[key]["type"] == "string" else "IntegerField") + "(max_length=25, blank=True, null=True, default=None" + (", choices=" + key.upper() + "_CHOICES" if "choices" in d[key].keys() else "" ) + ")")
#     if "choices" in d[key].keys():
#         l = ""
#         for c in d[key]["choices"]:
#             l += ("(" + str(c).upper()  + ", " +  str(c).upper() + "),\n")
#         print(key.upper()  + "_CHOICES = [" + l + "]")


class ProductElevator(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE)
    is_active = models.BooleanField(blank=True, default=True)
    installed_at = models.DateTimeField(blank=True, null=True)
    removed_at = models.DateTimeField(blank=True, null=True)
    installed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='product_installations')
    removed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                   related_name='product_removals')
    removal_reason = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['product'], condition=models.Q(is_active=True),
            name='visit_one_active_installation_per_product',
        )]


class WarrantyContract(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    reference = models.CharField(max_length=80)
    coverage_start = models.DateField()
    coverage_end = models.DateField()
    terms = models.TextField(blank=True, default='')
    exclusions = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(coverage_end__gte=models.F('coverage_start')),
                name='warranty_valid_coverage_period',
            ),
            models.UniqueConstraint(fields=['project', 'reference'], name='warranty_unique_project_reference'),
        ]


class WarrantyClaim(models.Model):
    PENDING = 'PENDING'
    COVERED = 'COVERED'
    DENIED = 'DENIED'
    STATUS_CHOICES = ((PENDING, 'در انتظار بررسی'), (COVERED, 'تحت پوشش'),
                      (DENIED, 'خارج از پوشش'))
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    contract = models.ForeignKey(WarrantyContract, on_delete=models.PROTECT, null=True, blank=True)
    visit = models.ForeignKey('Visit', on_delete=models.SET_NULL, null=True, blank=True)
    issue = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    decision_reason = models.TextField(blank=True, default='')
    opened_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='warranty_claims_opened')
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='warranty_claims_decided')
    opened_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)


class RepairCase(models.Model):
    rma_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    RECEIVED = 'RECEIVED'
    DIAGNOSING = 'DIAGNOSING'
    REPAIRING = 'REPAIRING'
    TESTING = 'TESTING'
    READY = 'READY'
    DELIVERED = 'DELIVERED'
    CANCELED = 'CANCELED'
    STATUS_CHOICES = tuple((state, state.title()) for state in (
        RECEIVED, DIAGNOSING, REPAIRING, TESTING, READY, DELIVERED, CANCELED,
    ))
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    client = models.ForeignKey('Client', on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='repair_cases')
    claim = models.ForeignKey(WarrantyClaim, on_delete=models.PROTECT, null=True, blank=True)
    serial_snapshot = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=RECEIVED)
    received_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    diagnosis = models.TextField(blank=True, default='')
    work_performed = models.TextField(blank=True, default='')
    test_result = models.TextField(blank=True, default='')
    loaner_product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True,
                                       related_name='loaner_repair_cases')
    loaner_due_at = models.DateField(null=True, blank=True)
    loaner_returned_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='repair_cases_created')

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(loaner_product__isnull=True)
                | ~models.Q(loaner_product=models.F('product')),
                name='repair_loaner_differs_from_product',
            ),
            models.UniqueConstraint(
                fields=['loaner_product'],
                condition=models.Q(loaner_product__isnull=False,
                                   loaner_returned_at__isnull=True),
                name='repair_one_open_loan_per_product',
            ),
        ]


class RepairEvent(models.Model):
    case = models.ForeignKey(RepairCase, on_delete=models.CASCADE, related_name='events')
    from_status = models.CharField(max_length=12, blank=True, default='')
    to_status = models.CharField(max_length=12)
    note = models.TextField(blank=True, default='')
    loaner_product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    loaner_due_at = models.DateField(null=True, blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    at = models.DateTimeField(auto_now_add=True)

# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import D
# from django.contrib.gis.db.models.functions import Distance

class Building(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True)
    APARTMENT = "Apartment"
    COMPLEX = "Complex"
    TYPES = (
        (APARTMENT, "Apartment"),
        (COMPLEX, "Complex"),
    )
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    type = models.CharField(max_length=10, choices=TYPES, default="Complex")
    parent = models.ForeignKey('Building', on_delete=models.CASCADE, related_name="parent_building", blank=True, null=True, default=None)
    address = models.TextField(blank=True, null=True, default=None)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_visiting = models.BooleanField(blank=True, default=False)
    code = models.CharField(max_length=25, unique=True)
    priority_score = models.FloatField(null=True, blank=True, db_index=True)
    
class BuildingElevator(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE)

class BuildingClient(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    # Null start on legacy rows means the beginning of management is unknown.
    start_at = models.DateTimeField(blank=True, null=True, default=None)
    end_at = models.DateTimeField(blank=True, null=True, default=None)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='managements_started')
    ended_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='managements_ended')
    start_reason = models.CharField(max_length=500, blank=True, default='')
    end_reason = models.CharField(max_length=500, blank=True, default='')

    def save(self, *args, **kwargs):
        if self.pk is None and self.start_at is None:
            self.start_at = timezone.now()
        if self.end_at is not None and self.start_at is not None and self.end_at <= self.start_at:
            raise ValidationError('Management end must be after its start.')
        return super().save(*args, **kwargs)

class Answer(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, null=True, blank=True, default=None)
    # survey_fill_out = models.ForeignKey(SurveyFillOut, on_delete=models.CASCADE, null=True, blank=True, default=None)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    score = models.IntegerField(blank=True, null=True, default=None)
    number = models.IntegerField(blank=True, null=True, default=None)
    bool = models.BooleanField(blank=True, null=True, default=None)
    text = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    price = models.BigIntegerField(blank=True, null=True, default=None)
    multichoice = models.ManyToManyField(
        AnswerChoice, blank=True, related_name='Answers')
    dropdown = models.ForeignKey(AnswerChoice, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='dropdown')
    radio = models.ForeignKey(AnswerChoice, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='radio')
    bool_is_expected = models.BooleanField(blank=True, null=True, default=None)
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(Answer, self).save(*args, **kwargs)


class PhotoType(models.Model):
    name = models.CharField(max_length=30)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=40, default="")
    min = models.IntegerField(blank=True, default=1)
    max = models.IntegerField(blank=True, default=20)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, null=True, blank=True, default=None)
    is_mandatory = models.BooleanField(blank=True, default=False)
    report_category = models.ForeignKey(
        ReportCategory, on_delete=models.CASCADE, blank=True, null=True, default=None)
    description = models.TextField(default="")
    is_for_supervision = models.BooleanField(blank=True, default=False)
    is_active = models.BooleanField(blank=True, default=True)


class Photo(models.Model):
    NOT_CHECKED = 'NOT_CHECKED'
    CONFIRMED = 'CONFIRMED'
    REJECTED = 'REJECTED'
    CONFIRMATION_CHOICES = (
        (NOT_CHECKED, 'NOT_CHECKED'),
        (CONFIRMED, 'CONFIRMED'),
        (REJECTED, 'REJECTED'),
    )

    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    type = models.ForeignKey(PhotoType, on_delete=models.CASCADE)
    link = models.URLField(blank=True, null=True, default=None)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE)
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)
    supervision_location_confirm = models.CharField(max_length=12, blank=True, choices=CONFIRMATION_CHOICES, default='NOT_CHECKED')
    supervision_confirm = models.CharField(max_length=12, blank=True, choices=CONFIRMATION_CHOICES, default='NOT_CHECKED')
    recognition_status = models.IntegerField(blank=True, null=True, default=None)
    is_deleted = models.BooleanField(default=False, blank=True)
    is_checked = models.BooleanField(default=False, blank=True)
    is_favourite = models.BooleanField(default=False, blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        super(Photo, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()

class VisitRate(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE)
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    photo_type = models.ForeignKey(PhotoType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    rate = models.IntegerField(validators=[MaxValueValidator(10000), MinValueValidator(0)])
    datetime_created = models.DateTimeField(blank=True, null=True, default=None)
    datetime_last_change = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        unique_together = (
            'created_by',
            'visit',
            'question_type',
            'photo_type',
        )

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        now = timezone.now()
        if not self.id:
            self.datetime_created = now
        self.datetime_last_change = now
        return super(VisitRate, self).save(*args, **kwargs)



##############################
# for omid:
##############################


class Census(models.Model):
    porslineid = models.CharField(max_length=20, null=True, default=None)
    province = models.CharField(max_length=60, null=True, default=None)
    city = models.CharField(max_length=60, null=True, default=None)
    storefront_photo = models.TextField(null=True, default=None)
    store_situation = models.TextField(null=True, default=None)
    store_name = models.CharField(max_length=120, null=True, default=None)
    store_owner = models.CharField(max_length=40, null=True, default=None)
    store_address = models.TextField(null=True, default=None)
    postalcode = models.CharField(max_length=10, null=True, default=None)
    phone = models.CharField(max_length=200, null=True, default=None)
    mobile = models.CharField(max_length=200, null=True, default=None)
    banknum = models.CharField(max_length=50, null=True, default=None)
    boardlable = models.CharField(max_length=150, null=True, default=None)
    meter = models.IntegerField(null=True, default=None)
    isavailable = models.BooleanField(null=True, default=None)
    hamakri = models.BooleanField(null=True, default=None)
    visitcard_photo = models.TextField(null=True, default=None)
    vitrin_photo = models.TextField(null=True, default=None)
    gift_photo = models.TextField(null=True, default=None)
    pop_photo = models.TextField(null=True, default=None)
    selfie_photo = models.TextField(null=True, default=None)
    promoter_code = models.CharField(max_length=50, null=True, default=None)
    location = models.CharField(max_length=60, null=True, default=None)
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True, default=None)
    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True, default=None)
    start_date = models.CharField(max_length=30, null=True, default=None)
    finish_date = models.CharField(max_length=30, null=True, default=None)
    photo = models.URLField(blank=True, null=True, default=None)


class FieldsTranstaltion(models.Model):
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=250, null=True)


class FoulAlarm(models.Model):
    is_deleted = models.BooleanField(blank=True, default=False)


###############################
# Ticketing:
###############################


class Ticket(models.Model):
    WAITING = 'W'
    ANSWERED = 'A'
    CLOSED = 'C'
    STATUS_CHOICES = (
        (WAITING, 'Waiting'),
        (ANSWERED, 'Answered'),
        (CLOSED, 'Closed'),
    )
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, blank=True, null=True, default=None)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, blank=True, null=True, default=None)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    title = models.CharField(max_length=35, null=True, blank=True, default=None)
    subject = models.CharField(max_length=60, blank=True, null=True, default=None)
    status = models.CharField(max_length=1, default='W', choices=STATUS_CHOICES, blank=True)
    is_deleted = models.BooleanField(blank=True, default=False)
    role_assignee = models.ForeignKey(Role, on_delete=models.CASCADE)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
            if self.visit is not None:
                self.building = self.visit.building
        self.datetime_last_change = timezone.now()
        return super(Ticket, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return super(Ticket, self).save(*args, **kwargs)


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    created_by_role_assignment = models.ForeignKey(RoleAssignment, on_delete=models.CASCADE, blank=True, null=True, default=None)
    body = models.TextField(blank=True, null=True, default=None)
    is_deleted = models.BooleanField(blank=True, default=False)
    parent = models.ForeignKey('TicketMessage', related_name='TicketMessageParent', on_delete=models.CASCADE, blank=True, null=True, default=None)
    
    # assignee =
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if self.created_by_role_assignment_id is None:
            self.created_by_role_assignment = RoleAssignment.objects.filter(
                user=self.created_by, project=self.ticket.project, is_deleted=False,
                role__is_active=True,
            ).order_by('pk').first()
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(TicketMessage, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return super(TicketMessage, self).save(*args, **kwargs)


class TicketMessageAttachment(models.Model):
    ticket_message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE)
    link = models.TextField()
    is_deleted = models.BooleanField(blank=True, default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return super(TicketMessageAttachment, self).save(*args, **kwargs)


class VisitRule(models.Model):
    title = models.CharField(max_length=40)
    description = models.TextField(default="")
    score_begin = models.IntegerField()
    score_end = models.IntegerField()
    result = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.score_begin <= self.score_end:
            raise ValidationError("score_begin must be less than or equal to score_end")
        
        # TODO: Prevent intersection between rules

        return super().save(*args, **kwargs)


class PriorityFactor(models.Model):
    """A weighted criterion of service priority, e.g. client tier or building sensitivity."""
    CLIENT = 'client'
    BUILDING = 'building'
    ELEVATOR = 'elevator'
    TARGETS = ((CLIENT, 'مشتری'), (BUILDING, 'ساختمان'), (ELEVATOR, 'آسانسور'))
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='priority_factors')
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True, default='')
    target = models.CharField(max_length=10, choices=TARGETS)
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=1,
                                 validators=[MinValueValidator(0), MaxValueValidator(100)])
    # Used for entities without a chosen option, so a missing value neither boosts nor sinks them.
    default_value = models.PositiveSmallIntegerField(default=50, validators=[MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('order', 'id')


class PriorityOption(models.Model):
    factor = models.ForeignKey(PriorityFactor, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=80)
    value = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('order', 'id')


class PriorityAssignment(models.Model):
    """The option a client, building or elevator has for one factor."""
    factor = models.ForeignKey(PriorityFactor, on_delete=models.CASCADE, related_name='assignments')
    option = models.ForeignKey(PriorityOption, on_delete=models.CASCADE, related_name='assignments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True, related_name='priority_assignments')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, null=True, blank=True, related_name='priority_assignments')
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE, null=True, blank=True, related_name='priority_assignments')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(name='priority_assignment_one_target', check=(
                models.Q(client__isnull=False, building__isnull=True, elevator__isnull=True)
                | models.Q(client__isnull=True, building__isnull=False, elevator__isnull=True)
                | models.Q(client__isnull=True, building__isnull=True, elevator__isnull=False))),
            models.UniqueConstraint(fields=['factor', 'client'], condition=models.Q(client__isnull=False),
                                    name='priority_unique_client_factor'),
            models.UniqueConstraint(fields=['factor', 'building'], condition=models.Q(building__isnull=False),
                                    name='priority_unique_building_factor'),
            models.UniqueConstraint(fields=['factor', 'elevator'], condition=models.Q(elevator__isnull=False),
                                    name='priority_unique_elevator_factor'),
        ]


class VisitAssignmentEvent(models.Model):
    """A field worker accepting or handing back an assigned visit; declines carry a reason for planners."""
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    ACTIONS = ((ACCEPTED, 'پذیرش'), (DECLINED, 'بازگرداندن'))
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='assignment_events')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='visit_assignment_events')
    action = models.CharField(max_length=10, choices=ACTIONS)
    reason = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-id')


class MaintenancePlan(models.Model):
    """Recurring service of one elevator; visit.maintenance opens each visit ahead of its due date."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='maintenance_plans')
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE, related_name='maintenance_plans')
    visit_type = models.ForeignKey(VisitType, on_delete=models.PROTECT, related_name='maintenance_plans')
    expert = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_plans')
    interval_days = models.PositiveSmallIntegerField(validators=[MinValueValidator(7), MaxValueValidator(730)])
    lead_days = models.PositiveSmallIntegerField(default=7, validators=[MaxValueValidator(60)])
    next_due = models.DateField()
    note = models.CharField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('next_due', 'id')


class Skill(models.Model):
    """A specialty such as control boards, hydraulic lifts or automatic doors."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('name', 'id')
        constraints = [models.UniqueConstraint(fields=['project', 'name'], name='skill_unique_name_per_project')]


class ServiceRequirement(models.Model):
    """What a service type asks of the worker: a skill at a minimum level (1-5)."""
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, related_name='requirements')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='requirements')
    min_level = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    # Required: workers below the level are not eligible. Preferred: lowers the fit only.
    is_required = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['visit_type', 'skill'], name='requirement_unique_skill_per_type')]


class ExpertProfile(models.Model):
    """Planning data of a field worker in one project; absent profile means the defaults."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expert_profiles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expert_profiles')
    # 1 (trainee) to 5 (senior); must reach a service type's complexity.
    grade = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    # Python weekdays (Mon=0 … Sun=6); the default is Saturday to Wednesday.
    work_days = models.JSONField(default=list)
    daily_capacity = models.PositiveSmallIntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(30)])
    max_open = models.PositiveSmallIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(100)])
    is_assignable = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['project', 'user'], name='expert_profile_unique')]


class ExpertSkill(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expert_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='holders')
    level = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'skill'], name='expert_skill_unique')]


class ExpertTimeOff(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_off')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ('start_date', 'id')
        constraints = [models.CheckConstraint(check=models.Q(end_date__gte=models.F('start_date')),
                                              name='time_off_valid_period')]


class AssignmentSetting(models.Model):
    """Project weights of the assignment score; a weight of 0 switches that factor off."""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='assignment_setting')
    skill_weight = models.DecimalField(max_digits=5, decimal_places=2, default=4, validators=[MinValueValidator(0), MaxValueValidator(10)])
    quality_weight = models.DecimalField(max_digits=5, decimal_places=2, default=3, validators=[MinValueValidator(0), MaxValueValidator(10)])
    workload_weight = models.DecimalField(max_digits=5, decimal_places=2, default=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    familiarity_weight = models.DecimalField(max_digits=5, decimal_places=2, default=1, validators=[MinValueValidator(0), MaxValueValidator(10)])
    # Skill and quality count this many times more for critical and high priority visits.
    urgent_boost = models.DecimalField(max_digits=4, decimal_places=2, default=1.5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    updated_at = models.DateTimeField(auto_now=True)
