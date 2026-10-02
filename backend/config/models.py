from django.db import models

# Create your models here.

from django.contrib.postgres.indexes import GinIndex

from auth_app.models import Project, Role, User


class Config(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField(blank=True, null=True, default=None)
    category = models.CharField(max_length=50, blank=True, null=True, default=None)

class AddIn(models.Model):
    key = models.CharField(max_length=24)
    name = models.CharField(max_length=40, blank=True, null=True, default=None)
    verbose_name = models.CharField(max_length=40, blank=True, null=True, default=None)
    app_model_name = models.CharField(max_length=150, blank=True, null=True, default=None)
    is_active = models.BooleanField(blank=True, default=True)


class NavMenu(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, default=None)
    title_fa = models.CharField(max_length=254, blank=True, null=True, default=None)
    active_icon = models.TextField(blank=True, null=True, default=None)
    active_icon_thumbnail = models.TextField(blank=True, null=True, default=None)
    deactive_icon = models.TextField(blank=True, null=True, default=None)
    deactive_icon_thumbnail = models.TextField(blank=True, null=True, default=None)
    priority = models.IntegerField(blank=True, null=True, default=None)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)
    is_landing = models.BooleanField(default=False)
    route = models.CharField(max_length=255, blank=True, null=True, default=None)

class MediaType(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True, default=None)
    title_fa = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_active = models.BooleanField(blank=True, null=True, default=True)

    def delete(self, *args, **kwargs):
        self.is_active = True
        return self.save()

class MediaManager(models.Model):
    class Client(models.IntegerChoices):
        PWA = 1
        LANDING = 2

    title = models.CharField(max_length=255, blank=True, null=True, default=None)
    title_fa = models.CharField(max_length=254, blank=True, null=True, default=None)
    image_1 = models.TextField(blank=True, null=True, default=None)
    image_1_alter = models.CharField(max_length=40, blank=True, null=True, default=None)
    image_1_thumbnail = models.TextField(blank=True, null=True, default=None)
    image_2 = models.TextField(blank=True, null=True, default=None)
    image_2_alter = models.CharField(max_length=40, blank=True, null=True, default=None)
    image_2_thumbnail = models.TextField(blank=True, null=True, default=None)
    client = models.IntegerField(choices=Client.choices, blank=True, null=True, default=None)
    type = models.ForeignKey(MediaType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    redirect_url = models.TextField(max_length=255, blank=True, null=True, default=None)
    page_url = models.TextField(max_length=255, blank=True, null=True, default=None)
    is_active = models.BooleanField(default=False, blank=True)
    body_copy = models.TextField(blank=True, null=True, default=None)

    def delete(self, *args, **kwargs):
        self.is_active = False
        return self.save()





class TagType(models.Model):
    name = models.CharField(max_length=40, null=True, default=None, blank=True)
    verbose = models.CharField(max_length=40, null=True, default=None, blank=True)


class TagManager(models.Model):
    title = models.CharField(max_length=255, null=True, default=None, blank=True)
    title_fa = models.CharField(max_length=255, null=True, default=None, blank=True)
    type = models.ForeignKey(TagType, on_delete=models.CASCADE, blank=True, null=True, default=None)
    icon = models.TextField(null=True, default=None)
    icon_thumbnail = models.TextField(null=True, default=None)
    image = models.TextField(null=True, default=None)
    image_thumbnail = models.TextField(null=True, default=None)
    priority = models.IntegerField(blank=True, default=0)
    is_active = models.BooleanField(blank=True, null=True, default=True)
    is_visible = models.BooleanField(blank=True, null=True, default=True)
    datetime_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    datetime_last_change = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        indexes = [
            GinIndex(fields=['title'], name='config_tagm_title_ef6aee_gin', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['title_fa'], name='config_tagm_title_f_fb3ae2_gin', opclasses=['gin_trgm_ops']),
        ]

    def delete(self, *args, **kwargs):
        self.is_active = False
        return self.save()
