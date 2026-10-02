"""Service priority: weighted factors, inheritance, recompute triggers, API scope and task ordering."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import (Building, BuildingClient, BuildingElevator, Client, Elevator, PriorityAssignment,
                          PriorityFactor, PriorityOption, UserClient, Visit, VisitType)
from visit.priority import explain, level, recompute_project


def grant(role, name, method):
    view, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
    flag = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'DELETE': 'can_delete'}[method]
    RoleView.objects.update_or_create(role=role, view_method_name=view, defaults={flag: True})


class PriorityTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Priority')
        self.manager = User.objects.create(username='prio-manager')
        self.expert = User.objects.create(username='prio-expert')
        self.manager_role = Role.objects.create(title='Prio manager', title_abbreviation='M', asset_scope='project')
        self.expert_role = Role.objects.create(title='Prio expert', title_abbreviation='P', asset_scope='assigned')
        RoleAssignment.objects.create(user=self.manager, role=self.manager_role, project=self.project)
        RoleAssignment.objects.create(user=self.expert, role=self.expert_role, project=self.project)
        for name, method in [('PriorityFactorListCreateView', 'GET'), ('PriorityFactorListCreateView', 'POST'),
                             ('PriorityFactorDetailView', 'PUT'), ('PriorityEntityView', 'GET'), ('PriorityEntityView', 'PUT'),
                             ('PriorityRankingView', 'GET')]:
            grant(self.manager_role, name, method)
        grant(self.expert_role, 'PriorityRankingView', 'GET')
        grant(self.expert_role, 'PromoterVisitsAPIView', 'GET')
        self.premium = Client.objects.create(project=self.project, name='Premium co')
        self.economy = Client.objects.create(project=self.project, name='Economy co')
        self.hospital = Building.objects.create(project=self.project, code='PRIO-H')
        self.office = Building.objects.create(project=self.project, code='PRIO-O')
        BuildingClient.objects.create(building=self.hospital, client=self.premium)
        BuildingClient.objects.create(building=self.office, client=self.economy)
        self.lift = Elevator.objects.create(project=self.project, title='Bed lift')
        self.office_lift = Elevator.objects.create(project=self.project, title='Office lift')
        BuildingElevator.objects.create(building=self.hospital, elevator=self.lift)
        BuildingElevator.objects.create(building=self.office, elevator=self.office_lift)
        self.tier = PriorityFactor.objects.create(project=self.project, name='Tier', target='client', weight=3, default_value=50)
        self.sensitivity = PriorityFactor.objects.create(project=self.project, name='Use', target='building', weight=1, default_value=40)
        self.top = PriorityOption.objects.create(factor=self.tier, label='Premium', value=100)
        self.low = PriorityOption.objects.create(factor=self.tier, label='Economy', value=20)
        self.medical = PriorityOption.objects.create(factor=self.sensitivity, label='Medical', value=100)
        PriorityAssignment.objects.create(factor=self.tier, option=self.top, client=self.premium)
        PriorityAssignment.objects.create(factor=self.tier, option=self.low, client=self.economy)
        PriorityAssignment.objects.create(factor=self.sensitivity, option=self.medical, building=self.hospital)
        recompute_project(self.project.pk)
        self.api = APIClient()

    def refresh(self, *rows):
        for row in rows:
            row.refresh_from_db()

    def test_weighted_scores_inherit_down_the_asset_tree(self):
        self.refresh(self.premium, self.hospital, self.lift, self.office, self.office_lift)
        self.assertEqual(self.premium.priority_score, 100)
        self.assertEqual(self.hospital.priority_score, 100)  # (3×100 + 1×100) / 4
        self.assertEqual(self.lift.priority_score, 100)
        self.assertEqual(self.office.priority_score, 25)  # (3×20 + 1×40 default) / 4
        self.assertEqual(level(self.hospital.priority_score)['key'], 'critical')
        parts = explain(self.project.pk, 'elevator', self.lift.pk)['parts']
        self.assertEqual({part['name']: part['inherited'] for part in parts}, {'Tier': True, 'Use': True})
        self.tier.weight = 0
        self.tier.save()
        recompute_project(self.project.pk)
        self.refresh(self.office)
        self.assertEqual(self.office.priority_score, 40)  # only the building default remains

    def test_management_transfer_recomputes_inherited_scores(self):
        with self.captureOnCommitCallbacks(execute=True):
            BuildingClient.objects.filter(building=self.office).delete()
            BuildingClient.objects.create(building=self.office, client=self.premium)
        self.refresh(self.office)
        self.assertEqual(self.office.priority_score, 85)  # (3×100 + 1×40) / 4

    def test_api_scope_and_entity_choices(self):
        self.api.force_authenticate(self.expert)
        self.assertEqual(self.api.get(f'/core/api/admin/priority/ranking/?p={self.project.pk}').status_code, 403)
        self.api.force_authenticate(self.manager)
        response = self.api.get(f'/core/api/admin/priority/ranking/?p={self.project.pk}&target=building')
        self.assertEqual([row['id'] for row in response.data['results']], [self.hospital.pk, self.office.pk])
        url = f'/core/api/admin/priority/entity/building/{self.office.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.put(url, {'choices': {str(self.sensitivity.pk): self.top.pk}}, format='json').status_code, 400)
        response = self.api.put(url, {'choices': {str(self.sensitivity.pk): self.medical.pk}}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['score'], 40.0)  # (3×20 + 1×100) / 4
        response = self.api.put(url, {'choices': {str(self.sensitivity.pk): None}}, format='json')
        self.assertEqual(response.data['score'], 25.0)
        other = Project.objects.create(name='Other priority')
        foreign = Building.objects.create(project=other, code='PRIO-X')
        self.assertEqual(self.api.get(f'/core/api/admin/priority/entity/building/{foreign.pk}/?p={self.project.pk}').status_code, 404)

    def test_factor_editing_retires_removed_options(self):
        self.api.force_authenticate(self.manager)
        url = f'/core/api/admin/priority/factors/{self.tier.pk}/?p={self.project.pk}'
        payload = {'name': 'Tier', 'target': 'client', 'weight': 3, 'default_value': 50,
                   'options': [{'id': self.top.pk, 'label': 'Premium', 'value': 90}]}
        self.assertEqual(self.api.put(url, payload, format='json').status_code, 200)
        self.assertFalse(PriorityAssignment.objects.filter(client=self.economy).exists())
        self.refresh(self.premium, self.economy)
        self.assertEqual(self.premium.priority_score, 90)
        self.assertEqual(self.economy.priority_score, 50)  # back to the factor default
        payload['target'] = 'building'
        self.assertEqual(self.api.put(url, payload, format='json').status_code, 400)

    def test_expert_tasks_are_ordered_by_priority(self):
        kind = VisitType.objects.create(project=self.project, title='Service')
        later = Visit.objects.create(type=kind, building=self.office, creator=self.manager, expert=self.expert, is_active=True)
        urgent = Visit.objects.create(type=kind, building=self.hospital, creator=self.manager, expert=self.expert, is_active=True)
        urgent.elevator.set([self.lift])
        self.api.force_authenticate(self.expert)
        response = self.api.get(f'/core/api/promoter/open_visits/list/?p={self.project.pk}')
        self.assertEqual([row['id'] for row in response.data], [urgent.pk, later.pk])
        self.assertEqual(response.data[0]['priority']['level']['key'], 'critical')

    def test_provision_command_previews_then_grants_and_adds_menu(self):
        from io import StringIO
        from django.core.management import call_command
        from auth_app.models import AdminMenu
        role = Role.objects.create(title='Ops', title_abbreviation='M', asset_scope='project')
        RoleAssignment.objects.create(user=self.manager, role=role, project=self.project)
        call_command('provision_priority_access', '--project', self.project.pk, '--role', role.pk, stdout=StringIO())
        self.assertFalse(RoleView.objects.filter(role=role).exists())
        call_command('provision_priority_access', '--project', self.project.pk, '--role', role.pk, '--apply', stdout=StringIO())
        self.assertTrue(RoleView.objects.filter(role=role, view_method_name__view_name='PriorityRankingView', can_view=True).exists())
        self.assertFalse(RoleView.objects.filter(role=role, view_method_name__view_name='PriorityFactorDetailView').exists())
        menu = AdminMenu.objects.get(role=role, frontend_route_url='/priority')
        self.assertTrue(menu.active_icon.startswith('data:image/svg+xml'))
        call_command('provision_priority_access', '--project', self.project.pk, '--role', role.pk, '--apply', '--manage', stdout=StringIO())
        self.assertTrue(RoleView.objects.filter(role=role, view_method_name__view_name='PriorityFactorDetailView', can_update=True).exists())
        self.assertEqual(AdminMenu.objects.filter(role=role, frontend_route_url='/priority').count(), 1)

