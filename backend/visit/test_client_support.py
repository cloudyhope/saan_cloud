from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from notification.models import InAppNotification
from visit.models import Building, BuildingClient, Client, Ticket, TicketMessage, UserClient


class ClientSupportTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Support one')
        self.other_project = Project.objects.create(name='Support two')
        self.user = User.objects.create(username='support-client')
        self.other = User.objects.create(username='support-other')
        self.staff = User.objects.create(username='support-staff')
        client_role = Role.objects.create(title='Support customer', title_abbreviation='C', asset_scope='client')
        staff_role = Role.objects.create(title='Support staff', title_abbreviation='S', asset_scope='project')
        RoleAssignment.objects.create(user=self.user, role=client_role, project=self.project)
        RoleAssignment.objects.create(user=self.other, role=client_role, project=self.project)
        RoleAssignment.objects.create(user=self.staff, role=staff_role, project=self.project)
        for view in ('ClientSupportTicketsAPIView', 'ClientSupportTicketDetailAPIView'):
            for method in ('GET', 'POST'):
                view_method, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
                RoleView.objects.create(role=client_role, view_method_name=view_method,
                                        can_view=method == 'GET', can_create=method == 'POST')
        for view, method, permission in (('TicketListCreateView', 'GET', 'can_view'),
                                         ('TicketMessageListCreateView', 'POST', 'can_create')):
            view_method, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
            RoleView.objects.create(role=staff_role, view_method_name=view_method, **{permission: True})
        client = Client.objects.create(project=self.project, name='Client one')
        UserClient.objects.create(user=self.user, client=client)
        self.building = Building.objects.create(project=self.project, code='SUPPORT-OWN')
        BuildingClient.objects.create(building=self.building, client=client)
        self.foreign = Building.objects.create(project=self.other_project, code='SUPPORT-FOREIGN')
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def list_url(self):
        return f'/core/api/client/support/tickets/?p={self.project.pk}'

    def detail_url(self, pk):
        return f'/core/api/client/support/tickets/{pk}/?p={self.project.pk}'

    def test_create_and_conversation_are_personal(self):
        self.assertEqual(self.api.post(self.list_url(), {
            'title': 'Access issue', 'body': 'Please help', 'building': self.foreign.pk,
        }, format='json').status_code, 400)
        response = self.api.post(self.list_url(), {
            'title': 'Access issue', 'body': 'Please help', 'building': self.building.pk,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        ticket_id = response.data['id']
        self.assertEqual(Ticket.objects.get(pk=ticket_id).role_assignee.asset_scope, 'project')
        self.assertEqual(InAppNotification.objects.filter(
            recipient=self.staff, kind='support_incoming', object_id=ticket_id).count(), 1)
        self.assertEqual(self.api.get(self.detail_url(ticket_id)).data['messages'][0]['body'], 'Please help')
        self.assertEqual(self.api.post(self.detail_url(ticket_id), {'body': 'More detail'}, format='json').status_code, 201)
        self.assertEqual(TicketMessage.objects.filter(ticket_id=ticket_id).count(), 2)
        self.assertEqual(InAppNotification.objects.filter(
            recipient=self.staff, kind='support_incoming', object_id=ticket_id).count(), 2)
        self.assertEqual(len(self.api.get(self.list_url()).data), 1)
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.get(self.detail_url(ticket_id)).status_code, 404)
        self.assertEqual(self.api.post(self.detail_url(ticket_id), {'body': 'No'}, format='json').status_code, 404)
        self.assertEqual(self.api.get(self.list_url()).data, [])
        self.assertFalse(InAppNotification.objects.filter(recipient=self.other).exists())

    def test_closed_ticket_cannot_receive_reply_and_requires_grant(self):
        ticket = Ticket.objects.create(project=self.project, creator=self.user,
                                       role_assignee=Role.objects.get(title='Support staff'))
        ticket.status = Ticket.CLOSED
        ticket.save()
        self.assertEqual(self.api.post(self.detail_url(ticket.pk), {'body': 'Again'}, format='json').status_code, 400)
        RoleView.objects.filter(role__title='Support customer',
                                view_method_name__view_name='ClientSupportTicketsAPIView',
                                view_method_name__method='GET').update(can_view=False)
        self.assertEqual(self.api.get(self.list_url()).status_code, 403)

    def test_no_staff_route_returns_service_unavailable_without_ticket(self):
        RoleView.objects.filter(role__title='Support staff',
                                view_method_name__view_name='TicketMessageListCreateView').update(can_create=False)
        response = self.api.post(self.list_url(), {'title': 'Issue', 'body': 'Message'}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Ticket.objects.exists())

    def test_staff_reply_creates_personal_notification(self):
        created = self.api.post(self.list_url(), {'title': 'Lift issue', 'body': 'Please check'}, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        self.api.force_authenticate(self.staff)
        response = self.api.post(
            f'/core/api/admin/ticket_message/list_create/?p={self.project.pk}',
            {'ticket': created.data['id'], 'body': 'We are checking'}, format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        item = InAppNotification.objects.get(recipient=self.user)
        self.assertEqual(item.project_id, self.project.pk)
        self.assertEqual(item.object_id, created.data['id'])
        self.api.force_authenticate(self.user)
        inbox = self.api.get(f'/core/api/notifications/?p={self.project.pk}')
        self.assertEqual(inbox.data['unread_count'], 1)
        self.assertEqual(inbox.data['results'][0]['id'], item.pk)
