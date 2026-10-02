"""Management dashboard data: project-wide only, scoped rows, period comparison."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Building, BuildingClient, Client, ClientVisitFeedback, Ticket, Visit, VisitReportSnapshot, VisitType


class DashboardTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Dashboard')
        self.other = Project.objects.create(name='Other dashboard')
        self.manager = User.objects.create(username='dash-manager')
        self.worker = User.objects.create(username='dash-worker', first_name='Ali')
        self.manager_role = Role.objects.create(title='Dash manager', title_abbreviation='M', asset_scope='project')
        self.worker_role = Role.objects.create(title='Dash worker', title_abbreviation='P', asset_scope='assigned')
        RoleAssignment.objects.create(user=self.manager, role=self.manager_role, project=self.project)
        RoleAssignment.objects.create(user=self.worker, role=self.worker_role, project=self.project)
        view, _ = ViewMethod.objects.get_or_create(view_name='AdminDashboardView', method='GET')
        for role in (self.manager_role, self.worker_role):
            RoleView.objects.create(role=role, view_method_name=view, can_view=True)
        self.building = Building.objects.create(project=self.project, code='DASH-1', verbose_name='Dash tower')
        client = Client.objects.create(project=self.project, name='Dash client')
        BuildingClient.objects.create(building=self.building, client=client)
        self.kind = VisitType.objects.create(project=self.project, title='Service')
        now = timezone.now()
        self.late = Visit.objects.create(type=self.kind, building=self.building, creator=self.manager, expert=self.worker,
                                         status=Visit.NOTVISITED, is_active=True, has_due_date=True,
                                         due_date=(now - timedelta(days=2)).date())
        self.done = Visit.objects.create(type=self.kind, building=self.building, creator=self.manager, expert=self.worker,
                                         status=Visit.APPROVED, is_active=True, start_datetime=now - timedelta(days=1))
        snapshot = VisitReportSnapshot.objects.create(visit=self.done, version=1, payload={}, checksum='x')
        VisitReportSnapshot.objects.filter(pk=snapshot.pk).update(created_at=now - timedelta(hours=20))
        ClientVisitFeedback.objects.create(visit=self.done, user=self.manager, rating=4)
        foreign_building = Building.objects.create(project=self.other, code='DASH-X')
        Visit.objects.create(type=VisitType.objects.create(project=self.other, title='Other'), building=foreign_building,
                             creator=self.manager, status=Visit.NOTVISITED, is_active=True)
        Ticket.objects.create(project=self.project, creator=self.manager, role_assignee=self.manager_role, status=Ticket.WAITING)
        self.api = APIClient()

    def get(self, user, query=''):
        self.api.force_authenticate(user)
        return self.api.get(f'/core/api/admin/dashboard/?p={self.project.pk}{query}')

    def test_project_manager_gets_scoped_rows(self):
        response = self.get(self.manager)
        self.assertEqual(response.status_code, 200, response.data)
        rows = {row['id']: row for row in response.data['visits']}
        self.assertEqual(set(rows), {self.late.pk, self.done.pk})
        self.assertEqual(rows[self.done.pk]['ra'], 4.0)
        self.assertIsNotNone(rows[self.done.pk]['co'])
        self.assertEqual(rows[self.late.pk]['du'], self.late.due_date.isoformat())
        self.assertEqual(rows[self.late.pk]['e'], self.worker.pk)
        self.assertEqual(response.data['lookups']['experts'][self.worker.pk], 'Ali')
        self.assertEqual(response.data['services']['tickets']['waiting'], 1)

    def test_field_role_and_bad_ranges_are_refused(self):
        self.assertEqual(self.get(self.worker).status_code, 403)
        self.assertEqual(self.get(self.manager, '&from=2026-10-05&to=2026-10-01').status_code, 400)
        self.assertEqual(self.get(self.manager, '&from=2024-01-01&to=2026-10-01').status_code, 400)
        self.assertEqual(self.get(self.manager, '&from=not-a-date').status_code, 400)
