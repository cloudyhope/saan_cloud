from django.db import models

from visit.models import Visit

from django.contrib.auth import get_user_model
User = get_user_model()

class Message(models.Model):
    type = models.CharField(max_length=30, null=False, blank=False)
    msg_pattern = models.TextField()
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()

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

from auth_app.models import Role, RoleAssignment
from visit.models import Elevator
class Conversation(models.Model):
    STATUS_CHOICES = (
        (1, 'Initial'),
        (2, 'In Progress'),
        (3, 'Closed'),
    )
    TYPE_CHOICES = (
        (1, 'Expert_Client'),
        (2, 'Admin_Client'),
        (3, 'Expert_Admin'),
    )
    title = models.CharField(max_length=255, null=False, blank=False)
    subject = models.CharField(max_length=255, null=False, blank=False)
    type = models.IntegerField(choices=TYPE_CHOICES, blank=True, null=True, default=None)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, blank=True, null=True, default=None)
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE, blank=True, null=True, default=None)
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    datetime_last_changed = models.DateTimeField(auto_now=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    assigned_role = models.ForeignKey(Role, on_delete=models.CASCADE, blank=True, null=True, default=None)
    assigned_person = models.ForeignKey(RoleAssignment, on_delete=models.CASCADE, blank=True, null=True, default=None)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()


class ConversationMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    body = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    is_seen = models.BooleanField(default=False)
    parent = models.ForeignKey('ConversationMessage', null=True, blank=True, on_delete=models.CASCADE,  related_name='ConversationMessageParent')
    datetime_created = models.DateTimeField(auto_now_add=True, blank=True)
    datetime_last_changed = models.DateTimeField(auto_now=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()




