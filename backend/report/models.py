from django.db import models
from visit.models import Census

# Create your models here.


class DateConvert(models.Model):
    jalali_date = models.CharField(max_length=12)
    miladi_datetime = models.DateTimeField()
    miladi_date = models.DateField(blank=True, null=True, default=None)
    
    miladi_year = models.IntegerField(null=True, blank=True, default=None)
    miladi_month = models.IntegerField(null=True, blank=True, default=None)
    miladi_day = models.IntegerField(null=True, blank=True, default=None)
    jalali_year = models.IntegerField(null=True, blank=True, default=None)
    jalali_month = models.IntegerField(null=True, blank=True, default=None)
    jalali_day = models.IntegerField(null=True, blank=True, default=None)
    
    jalali_month_name = models.CharField(max_length=16, null=True, blank=True, default=None)
    miladi_month_name = models.CharField(max_length=16, null=True, blank=True, default=None)

    jalali_season_name = models.CharField(max_length=16, null=True, blank=True, default=None)
    miladi_season_name = models.CharField(max_length=16, null=True, blank=True, default=None)

    jalali_year_quarter = models.IntegerField(null=True, blank=True, default=None)
    miladi_year_quarter = models.IntegerField(null=True, blank=True, default=None)
    
    miladi_day_of_the_week = models.IntegerField(null=True, blank=True, default=None)
    jalali_day_of_the_week = models.IntegerField(null=True, blank=True, default=None)
    
    miladi_week_no = models.IntegerField(null=True, blank=True, default=None)
    jalali_week_no = models.IntegerField(null=True, blank=True, default=None)
    custom_week_no = models.IntegerField(null=True, blank=True, default=None)
    
    project_week_no = models.IntegerField(null=True, blank=True, default=None)
    
    miladi_day_name = models.CharField(max_length=10, null=True, blank=True, default=None)
    jalali_day_name = models.CharField(max_length=10, null=True, blank=True, default=None)



class ReportCensus(models.Model):
    cencus = models.ForeignKey(Census, on_delete=models.CASCADE, null=True, default=None, blank=True)
    start_date = models.CharField(max_length=12)
    boardlable = models.CharField(max_length=150, null=True, default=None)
    store_name = models.CharField(max_length=120, null=True, default=None)
    province = models.CharField(max_length=60, null=True, default=None)
    city = models.CharField(max_length=60, null=True, default=None)
    
class DateMatch(models.Model):
    month = models.CharField(max_length=20, null=True, blank=True, default=None)
    datetime = models.DateTimeField(null=True, blank=True, default=None)
    date = models.DateField(null=True, blank=True, default=None)
    number = models.BigIntegerField(null=True, blank=True, default=None)
    