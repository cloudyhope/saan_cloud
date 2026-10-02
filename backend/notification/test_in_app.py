from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment
from notification.in_app import notify_support_reply
from notification.models import InAppNotification
from visit.models import Ticket, TicketMessage


class InAppNotificationTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Inbox one')
        self.other_project = Project.objects.create(name='Inbox two')
        self.user = User.objects.create(username='inbox-user')
        self.other = User.objects.create(username='inbox-other')
        self.role = Role.objects.create(title='Inbox client', title_abbreviation='C', asset_scope='client')
        RoleAssignment.objects.create(user=self.user, role=self.role, project=self.project)
        RoleAssignment.objects.create(user=self.other, role=self.role, project=self.project)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def create_item(self, recipient=None, project=None, key='event:1'):
        return InAppNotification.objects.create(
            recipient=recipient or self.user, project=project or self.project,
            source_key=key, kind='support_reply', title='Reply', object_id=3,
        )

    def test_self_inbox_and_read_are_project_scoped(self):
        own = self.create_item()
        other = self.create_item(recipient=self.other)
        foreign = self.create_item(project=self.other_project)
        url = f'/core/api/notifications/?p={self.project.pk}'
        response = self.api.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.data['results']], [own.pk])
        self.assertEqual(response.data['unread_count'], 1)
        self.assertEqual(self.api.post(f'/core/api/notifications/{other.pk}/read/?p={self.project.pk}').status_code, 404)
        self.assertEqual(self.api.post(f'/core/api/notifications/{foreign.pk}/read/?p={self.project.pk}').status_code, 404)
        self.assertEqual(self.api.get(f'/core/api/notifications/?p={self.other_project.pk}').status_code, 403)
        read_url = f'/core/api/notifications/{own.pk}/read/?p={self.project.pk}'
        self.assertEqual(self.api.post(read_url).status_code, 200)
        first_read_at = InAppNotification.objects.get(pk=own.pk).read_at
        self.assertEqual(self.api.post(read_url).status_code, 200)
        self.assertEqual(InAppNotification.objects.get(pk=own.pk).read_at, first_read_at)
        self.assertEqual(self.api.get(url).data['unread_count'], 0)

    def test_read_all_validation_and_membership_revocation(self):
        self.create_item()
        self.create_item(key='event:2')
        url = f'/core/api/notifications/?p={self.project.pk}'
        self.assertEqual(self.api.get(url + '&limit=0').status_code, 400)
        self.assertEqual(self.api.get(url + '&offset=-1').status_code, 400)
        self.assertEqual(self.api.get('/core/api/notifications/?p=no').status_code, 400)
        self.assertEqual(self.api.post(f'/core/api/notifications/read-all/?p={self.project.pk}').data['updated'], 2)
        self.assertEqual(self.api.get(url).data['unread_count'], 0)
        RoleAssignment.objects.filter(user=self.user, project=self.project).update(is_deleted=True)
        self.assertEqual(self.api.get(url).status_code, 403)
        self.api.force_authenticate(user=None)
        self.assertEqual(self.api.get(url).status_code, 401)

    def test_support_reply_is_idempotent_and_only_notifies_creator(self):
        ticket = Ticket.objects.create(project=self.project, creator=self.user, role_assignee=self.role)
        reply = TicketMessage.objects.create(ticket=ticket, created_by=self.other, body='Handled')
        notify_support_reply(ticket, reply)
        notify_support_reply(ticket, reply)
        self.assertEqual(InAppNotification.objects.filter(recipient=self.user).count(), 1)
        self.assertEqual(InAppNotification.objects.get(recipient=self.user).object_id, ticket.pk)
        own_reply = TicketMessage.objects.create(ticket=ticket, created_by=self.user, body='Thanks')
        notify_support_reply(ticket, own_reply)
        self.assertEqual(InAppNotification.objects.count(), 1)
