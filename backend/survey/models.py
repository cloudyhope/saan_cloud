from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from auth_app.models import FieldValidation, Province, City, Project
# Create your models here.


class SurveyReportCategory(models.Model):
    name = models.CharField(max_length=30)
    verbose_name = models.CharField(max_length=30)


class SurveyQuestionType(models.Model):
    name = models.CharField(max_length=30)
    verbose_name = models.CharField(max_length=40, default="")
    is_mandatory = models.BooleanField(blank=True, default=False)
    survey_report_category = models.ForeignKey(
        SurveyReportCategory, on_delete=models.CASCADE, blank=True, null=True, default=None)
    description = models.TextField(default="")
    has_score = models.BooleanField(blank=True, default=False)
    score_depends_on = models.ForeignKey('SurveyQuestionType', related_name="score_depends_on_question_type", on_delete=models.CASCADE, blank=True, null=True, default=None)
    score_min = models.IntegerField(blank=True, null=True, default=None)
    score_max = models.IntegerField(blank=True, null=True, default=None)
    prevents_visit_if_score_lte = models.IntegerField(blank=True, null=True, default=None)
    is_active = models.BooleanField(blank=True, default=True)

from config.models import AddIn
class Survey(models.Model):
    name = models.CharField(max_length=40, blank=True, null=True, default=None)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, default=None)
    category = models.IntegerField(blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=40, blank=True, null=True, default=None)
    is_active = models.BooleanField(blank=True, default=True)
    icon = models.TextField(blank=True, null=True, default=None)
    has_phone_verification = models.BooleanField(blank=True, null=True, default=False)
    sms_text = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_mandatory_city = models.BooleanField(blank=True, null=True, default=False)
    add_ins = models.ManyToManyField(AddIn)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(Survey, self).save(*args, **kwargs)


from visit.models import AnswerChoice
from visit.models import AnswerType
class SurveyQuestion(models.Model):
    survey_question_type = models.ForeignKey(
        SurveyQuestionType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    text = models.TextField()
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, null=True, default=1)
    validation = models.ForeignKey(FieldValidation, on_delete=models.CASCADE, null=True, blank=True, default=None)
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
    answer_choices = models.ManyToManyField(
        AnswerChoice, related_name='Survey_Valid_Answers')
    dropdown_choices = models.ManyToManyField(AnswerChoice, related_name='survey_dropdown_choices')
    radio_choices = models.ManyToManyField(AnswerChoice, related_name='survey_radio_choices')
    customer_category = models.CharField(
        max_length=30, default=None, blank=True, null=True)
    is_mandatory = models.BooleanField(blank=True, default=False)
    is_active = models.BooleanField(default=True, blank=True)
    survey_report_category = models.ForeignKey(
        SurveyReportCategory, on_delete=models.CASCADE, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    is_for_decision = models.BooleanField(blank=True, default=False)
    decision_rank = models.IntegerField(blank=True, null=True, default=None)


class OuterEntryConfig(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, blank=True, null=True, default=None)
    building = models.ForeignKey('visit.Building', on_delete=models.CASCADE, blank=True, null=True, default=None)
    url = models.TextField(blank=True, null=True, default=None)
    qr_icon = models.TextField(blank=True, null=True, default=None)
    image = models.TextField(blank=True, null=True, default=None)
    logo = models.TextField(blank=True, null=True, default=None)

# from visit.models import Visit
class SurveyFillOut(models.Model):
    INITIAL = '0'
    COMPLETED = '1'
    CONFIRMED = '2'
    STATUS_CHOICES = (
        (INITIAL, 'Initial'),
        (COMPLETED, 'Completed'),
        (CONFIRMED, 'Confirmed'),
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    visit = models.ForeignKey(to='visit.Visit', on_delete=models.CASCADE, blank=True, null=True, default=None)
    outer_entry = models.ForeignKey(OuterEntryConfig, on_delete=models.CASCADE, blank=True, null=True, default=None)
    outer_entry_int_user_id = models.BigIntegerField(blank=True, null=True, default=None)
    device_id = models.TextField(blank=True, null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, null=True, blank=True, default=None)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True, default=None)
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    phone_verified = models.BooleanField(blank=True, default=False)
    phone_number = models.CharField(max_length=16, blank=True, null=True, default=None)
    is_closed = models.BooleanField(blank=True, default=False)
    is_deleted = models.BooleanField(blank=True, default=False)
    status = models.CharField(max_length=1, default='0', choices=STATUS_CHOICES, blank=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)

    @property
    def final_score(self):
        """Sum up scores in fillout dropdown/radio answers and return the result"""
        result = 0

        questions = SurveyQuestion.objects.filter(survey=self.survey)
        answers = SurveyAnswer.objects.filter(survey_fill_out=self, survey_question__in=questions)
        
        for answer in answers:
            if answer.dropdown is not None:
                result += (answer.dropdown.score or 0)
            elif answer.radio is not None:
                result += (answer.radio.score or 0)
                
        return result
    
    @property
    def final_result(self):
        score = self.final_score

        try:
            rule = SurveyRule.objects.get(survey=self.survey, score_begin__lte=score, score_end__gt=score)
            return rule.result

        except SurveyRule.DoesNotExist:
            return None


    class Meta:
        unique_together = ('survey', 'phone_number', 'is_deleted',)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.phone_verified = False
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(SurveyFillOut, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()


class FillOutPhoneVerification(models.Model):
    phone_number = models.CharField(max_length=16)
    survey_fill_out = models.ForeignKey(SurveyFillOut, on_delete=models.CASCADE)
    code = models.CharField(max_length=128, blank=True)
    verification_token = models.TextField(blank=True)
    datetime_requested = models.DateTimeField(blank=True, null=True, default=None)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_requested = timezone.now()
        return super(FillOutPhoneVerification, self).save(*args, **kwargs)

class SurveyAnswer(models.Model):
    survey_fill_out = models.ForeignKey(SurveyFillOut, on_delete=models.CASCADE, null=True, blank=True, default=None)
    survey_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    score = models.IntegerField(blank=True, null=True, default=None)
    number = models.IntegerField(blank=True, null=True, default=None)
    bool = models.BooleanField(blank=True, null=True, default=None)
    text = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    price = models.BigIntegerField(blank=True, null=True, default=None)
    multichoice = models.ManyToManyField(
        AnswerChoice, blank=True, related_name='SurveyAnswers')
    dropdown = models.ForeignKey(AnswerChoice, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='survey_dropdown')
    radio = models.ForeignKey(AnswerChoice, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name='survey_radio')
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
        return super(SurveyAnswer, self).save(*args, **kwargs)


class SurveyPhotoType(models.Model):
    name = models.CharField(max_length=30)
    verbose_name = models.CharField(max_length=40, default="")
    min = models.IntegerField(blank=True, default=1)
    max = models.IntegerField(blank=True, default=20)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, blank=True, null=True, default=None)
    survey_question = models.ForeignKey(
        SurveyQuestion, on_delete=models.CASCADE, null=True, blank=True, default=None)
    is_mandatory = models.BooleanField(blank=True, default=False)
    survey_report_category = models.ForeignKey(
        SurveyReportCategory, on_delete=models.CASCADE, blank=True, null=True, default=None)
    description = models.TextField(default="")
    is_active = models.BooleanField(blank=True, default=True)


class SurveyPhoto(models.Model):
    NOT_CHECKED = 'NOT_CHECKED'
    CONFIRMED = 'CONFIRMED'
    REJECTED = 'REJECTED'
    CONFIRMATION_CHOICES = (
        (NOT_CHECKED, 'NOT_CHECKED'),
        (CONFIRMED, 'CONFIRMED'),
        (REJECTED, 'REJECTED'),
    )

    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, default=None)
    survey_photo_type = models.ForeignKey(SurveyPhotoType, on_delete=models.CASCADE)
    survey_fill_out = models.ForeignKey(SurveyFillOut, on_delete=models.CASCADE, null=True, blank=True, default=None)
    link = models.URLField(blank=True, null=True, default=None)
    longitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=22, decimal_places=16, blank=True, null=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_last_change = models.DateTimeField(blank=True)
    recognition_status = models.IntegerField(blank=True, null=True, default=None)
    supervision_location_confirm = models.CharField(max_length=12, blank=True, choices=CONFIRMATION_CHOICES, default='NOT_CHECKED')
    supervision_confirm = models.CharField(max_length=12, blank=True, choices=CONFIRMATION_CHOICES, default='NOT_CHECKED')
    is_deleted = models.BooleanField(default=False, blank=True)
    is_checked = models.BooleanField(default=False, blank=True)
    is_favourite = models.BooleanField(default=False, blank=True)


    def save(self, *args, **kwargs):
        # On save, update timestamps. but not on edit.
        if not self.id:
            self.datetime_created = timezone.now()
        self.datetime_last_change = timezone.now()
        return super(SurveyPhoto, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()


class SurveyRule(models.Model):
    title = models.CharField(max_length=40)
    description = models.TextField(default="")
    score_begin = models.IntegerField()
    score_end = models.IntegerField()
    result = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.score_begin <= self.score_end:
            raise ValidationError("score_begin must be less than or equal to score_end")
        
        # TODO: Check intersection between rules
        #survey_rules = SurveyRule.objects.filter(survey=self.survey)

        return super().save(*args, **kwargs)
