from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Building, Ticket, TicketMessage, Visit, VisitType


class ExpertSupportTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Expert support')
        self.other_project = Project.objects.create(name='Other project')
        self.expert = User.objects.create(username='expert-support')
        self.other_expert = User.objects.create(username='other-expert-support')
        self.staff = User.objects.create(username='staff-support')
        self.role = Role.objects.create(title='Field expert', title_abbreviation='P', asset_scope='assigned')
        self.staff_role = Role.objects.create(title='Support office', title_abbreviation='S', asset_scope='project')
        RoleAssignment.objects.create(user=self.expert, role=self.role, project=self.project)
        RoleAssignment.objects.create(user=self.other_expert, role=self.role, project=self.project)
        RoleAssignment.objects.create(user=self.staff, role=self.staff_role, project=self.project)
        for name in ('ExpertSupportTicketsAPIView', 'ExpertSupportTicketDetailAPIView'):
            for method, capability in (('GET', 'can_view'), ('POST', 'can_create')):
                view, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
                RoleView.objects.create(role=self.role, view_method_name=view, **{capability: True})
        for name, method, capability in (('TicketListCreateView', 'GET', 'can_view'),
                                         ('TicketMessageListCreateView', 'POST', 'can_create')):
            view, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
            RoleView.objects.create(role=self.staff_role, view_method_name=view, **{capability: True})
        visit_type = VisitType.objects.create(title='Expert service', project=self.project)
        self.building = Building.objects.create(project=self.project, code='EXPERT-OWN')
        self.other_building = Building.objects.create(project=self.project, code='EXPERT-OTHER')
        foreign_building = Building.objects.create(project=self.other_project, code='EXPERT-FOREIGN')
        self.visit = Visit.objects.create(type=visit_type, building=self.building,
                                          creator=self.staff, expert=self.expert)
        self.other_visit = Visit.objects.create(type=visit_type, building=self.other_building,
                                                creator=self.staff, expert=self.other_expert)
        self.foreign_visit = Visit.objects.create(type=visit_type, building=foreign_building,
                                                  creator=self.staff, expert=self.expert)
        self.api = APIClient()
        self.api.force_authenticate(self.expert)

    def list_url(self, project=None):
        return f'/core/api/expert/support/tickets/?p={project or self.project.pk}'

    def detail_url(self, pk, project=None):
        return f'/core/api/expert/support/tickets/{pk}/?p={project or self.project.pk}'

    def test_scoped_ticket_and_personal_conversation(self):
        for visit in (self.other_visit, self.foreign_visit):
            response = self.api.post(self.list_url(), {
                'title': 'Question', 'body': 'Message', 'visit': visit.pk,
            }, format='json')
            self.assertEqual(response.status_code, 400, response.data)
        response = self.api.post(self.list_url(), {
            'title': 'Question', 'body': 'Message', 'building': self.other_building.pk,
        }, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        response = self.api.post(self.list_url(), {
            'title': 'Question', 'body': 'Message', 'visit': self.visit.pk,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        ticket_id = response.data['id']
        self.assertEqual(Ticket.objects.get(pk=ticket_id).building_id, self.building.pk)
        self.assertEqual(self.api.get(self.detail_url(ticket_id)).data['messages'][0]['body'], 'Message')
        self.assertEqual(self.api.post(self.detail_url(ticket_id), {'body': 'Reply'}, format='json').status_code, 201)
        self.assertEqual(TicketMessage.objects.filter(ticket_id=ticket_id).count(), 2)
        self.api.force_authenticate(self.other_expert)
        self.assertEqual(self.api.get(self.detail_url(ticket_id)).status_code, 404)
        self.assertEqual(self.api.post(self.detail_url(ticket_id), {'body': 'No'}, format='json').status_code, 404)
        self.assertEqual(self.api.get(self.list_url()).data, [])

    def test_project_grant_and_closed_ticket_boundaries(self):
        ticket = Ticket.objects.create(project=self.project, creator=self.expert,
                                       role_assignee=self.staff_role, visit=self.visit)
        ticket.status = Ticket.CLOSED
        ticket.save()
        self.assertEqual(self.api.post(self.detail_url(ticket.pk), {'body': 'Again'}, format='json').status_code, 400)
        self.assertEqual(self.api.get(self.detail_url(ticket.pk, self.other_project.pk)).status_code, 403)
        RoleView.objects.filter(role=self.role,
                                view_method_name__view_name='ExpertSupportTicketsAPIView',
                                view_method_name__method='GET').update(can_view=False)
        self.assertEqual(self.api.get(self.list_url()).status_code, 403)

    def test_missing_staff_route_does_not_create_ticket(self):
        RoleView.objects.filter(role=self.staff_role,
                                view_method_name__view_name='TicketMessageListCreateView').update(can_create=False)
        response = self.api.post(self.list_url(), {
            'title': 'Question', 'body': 'Message', 'visit': self.visit.pk,
        }, format='json')
        self.assertEqual(response.status_code, 503, response.data)
        self.assertFalse(Ticket.objects.exists())

    def test_retired_legacy_conversation_urls_are_unavailable(self):
        for path in ('conversation/list_create/', 'conversation_message/list_create/'):
            self.assertEqual(self.api.get('/utils/api/v1/' + path).status_code, 404)
