from django.conf import settings
from django.db import models

from django.contrib.auth import get_user_model
User = get_user_model()

class MessageTemplate(models.Model):
    key = models.CharField(max_length=30, null=False, blank=False, unique=True)
    type = models.CharField(max_length=10, default="SMS") # OR EMAIL
    view = models.CharField(max_length=255, blank=True, null=True, default=None)
    path = models.CharField(max_length=255, blank=True, null=True, default=None)
    to = models.CharField(max_length=100, blank=True, null=True, default=None)
    msg_template = models.TextField()
    url_name = models.CharField(max_length=255, blank=True, null=True, default=None)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        return self.save()


class InAppNotification(models.Model):
    """A project-scoped, personal activity item with an idempotent event key."""

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='in_app_notifications')
    project = models.ForeignKey('auth_app.Project', on_delete=models.CASCADE)
    source_key = models.CharField(max_length=100)
    kind = models.CharField(max_length=40)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=240, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['recipient', 'project', 'source_key'], name='unique_personal_notification_event')]
        indexes = [models.Index(fields=['recipient', 'project', '-created_at'],
                                name='notif_personal_inbox_idx')]

