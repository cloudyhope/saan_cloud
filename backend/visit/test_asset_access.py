"""Project/owner/assignment boundaries and atomic client requests."""
import uuid
from io import BytesIO
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APIClient
from config.models import NavMenu
from notification.models import InAppNotification
from auth_app.models import (Project, Role, RoleAssignment, RoleView, ViewMethod,
                             Supervisor, ModelField, RoleViewModelField)
from visit.models import (Answer, AnswerChoice, AnswerType, Building, BuildingClient, BuildingElevator,
                          Client, Elevator, Photo, PhotoType, Product, ProductElevator, ProductModel, Question,
                          QuestionType, UserClient, Visit, VisitType, VisitReportSnapshot, ServiceRequestSubmission,
                          Ticket, TicketMessage, TicketMessageAttachment)


class AssetAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='A')
        self.foreign_project = Project.objects.create(name='B')
        self.user = User.objects.create(username='local-client-scope')
        self.other_user = User.objects.create(username='other-local-client')
        self.role = Role.objects.create(title='Client', title_abbreviation='C', asset_scope='client')
        self.manager = Role.objects.create(title='Manager', title_abbreviation='M', asset_scope='project')
        self.expert = Role.objects.create(title='Expert', title_abbreviation='P', asset_scope='assigned')
        self.supervisor = Role.objects.create(title='Supervisor', title_abbreviation='V', asset_scope='supervised')
        RoleAssignment.objects.create(user=self.user, role=self.role, project=self.project)
        self.client = Client.objects.create(name='Owned client', project=self.project)
        self.other_client = Client.objects.create(name='Other client', project=self.project)
        UserClient.objects.create(user=self.user, client=self.client)
        UserClient.objects.create(user=self.other_user, client=self.other_client)
        self.building = Building.objects.create(code='A-OWN', project=self.project)
        self.second = Building.objects.create(code='A-SECOND', project=self.project)
        self.other = Building.objects.create(code='A-OTHER', project=self.project)
        self.foreign = Building.objects.create(code='B-OTHER', project=self.foreign_project)
        BuildingClient.objects.create(building=self.building, client=self.client)
        BuildingClient.objects.create(building=self.second, client=self.client)
        BuildingClient.objects.create(building=self.other, client=self.other_client)
        self.elevator = Elevator.objects.create(title='Owned', project=self.project)
        self.extra_elevator = Elevator.objects.create(title='Extra', project=self.project)
        self.second_elevator = Elevator.objects.create(title='Second', project=self.project)
        self.other_elevator = Elevator.objects.create(title='Other', project=self.project)
        self.foreign_elevator = Elevator.objects.create(title='Foreign', project=self.foreign_project)
        for building, elevator in ((self.building, self.elevator), (self.building, self.extra_elevator),
                                   (self.second, self.second_elevator), (self.other, self.other_elevator),
                                   (self.foreign, self.foreign_elevator)):
            BuildingElevator.objects.create(building=building, elevator=elevator)
        self.model = ProductModel.objects.create(name='Owned model', project=self.project)
        self.part = Product.objects.create(model=self.model, project=self.project, serial_number='LOCAL-OWN-SN')
        ProductElevator.objects.create(product=self.part, elevator=self.elevator)
        self.other_model = ProductModel.objects.create(name='Other model', project=self.project)
        self.other_part = Product.objects.create(model=self.other_model, project=self.project, serial_number='LOCAL-OTHER-SN')
        ProductElevator.objects.create(product=self.other_part, elevator=self.other_elevator)
        self.visit_type = VisitType.objects.create(title='Check', project=self.project)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def grant(self, name, method='GET', role=None):
        vm, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
        return RoleView.objects.get_or_create(role=role or self.role, view_method_name=vm, defaults={
            'can_view': method == 'GET', 'can_create': method == 'POST',
            'can_update': method in ('PATCH', 'PUT'), 'can_delete': method == 'DELETE',
        })[0]

    def url(self, entity, suffix='ListCreate/'):
        return f'/api/visit/{entity}{suffix}?p={self.project.pk}'

    def as_role(self, role):
        RoleAssignment.objects.filter(user=self.user).update(is_deleted=True)
        RoleAssignment.objects.create(user=self.user, role=role, project=self.project)

    def request(self, rows=None, **changes):
        self.grant('ServiceRequestCreate', 'POST')
        data = {'type': self.visit_type.pk, 'request_key': str(uuid.uuid4()), 'buildings': rows or [
            {'building': self.building.pk, 'elevators': [self.elevator.pk]},
        ]}
        data.update(changes)
        return self.api.post(f'/core/api/service_request/create/?p={self.project.pk}', data, format='json')

    def test_client_lists_only_owned_assets_across_all_entity_apis(self):
        expected = {
            'Client': {self.client.pk}, 'Building': {self.building.pk, self.second.pk},
            'Elevator': {self.elevator.pk, self.extra_elevator.pk, self.second_elevator.pk},
            'Product': {self.part.pk}, 'ProductModel': {self.model.pk},
        }
        for entity, ids in expected.items():
            with self.subTest(entity=entity):
                self.grant(entity + 'ListCreateAPIView')
                response = self.api.get(self.url(entity))
                self.assertEqual(response.status_code, 200)
                self.assertEqual({row['id'] for row in response.data}, ids)
        for entity, expected_count in (('BuildingClient', 2), ('BuildingElevator', 3),
                                       ('ProductElevator', 1), ('UserClient', 1)):
            self.grant(entity + 'ListCreateAPIView')
            response = self.api.get(self.url(entity))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), expected_count)

    def test_client_cannot_get_patch_delete_someone_elses_building(self):
        for method in ('GET', 'PATCH', 'DELETE'):
            self.grant('BuildingEditsAPIView', method)
            response = getattr(self.api, method.lower())(self.url('Building', f'Edits/{self.other.pk}/'),
                                                         {'verbose_name': 'Forbidden'} if method == 'PATCH' else None)
            self.assertEqual(response.status_code, 404)
        self.other.refresh_from_db()
        self.assertIsNone(self.other.verbose_name)

    def test_omitting_me_cannot_expand_client_scope(self):
        self.grant('BuildingClientListCreateAPIView')
        for flag in ('', '&me=false', '&me=true', '&me=0'):
            response = self.api.get(self.url('BuildingClient') + flag)
            self.assertEqual({row['building']['id'] for row in response.data}, {self.building.pk, self.second.pk})

    def test_unassigned_legacy_building_is_not_exposed(self):
        legacy = Building.objects.create(code='UNASSIGNED')
        self.as_role(self.manager)
        self.grant('BuildingEditsAPIView', role=self.manager)
        self.assertEqual(self.api.get(self.url('Building', f'Edits/{legacy.pk}/')).status_code, 404)

    def test_project_role_never_sees_other_project(self):
        self.as_role(self.manager)
        self.grant('BuildingListCreateAPIView', role=self.manager)
        response = self.api.get(self.url('Building'))
        self.assertEqual({row['id'] for row in response.data}, {self.building.pk, self.second.pk, self.other.pk})
        self.grant('BuildingEditsAPIView', role=self.manager)
        self.assertEqual(self.api.get(self.url('Building', f'Edits/{self.foreign.pk}/')).status_code, 404)

    def test_project_in_payload_cannot_move_asset(self):
        self.as_role(self.manager)
        self.grant('BuildingEditsAPIView', 'PATCH', self.manager)
        response = self.api.patch(self.url('Building', f'Edits/{self.building.pk}/'),
                                  {'project': self.foreign_project.pk})
        self.assertEqual(response.status_code, 400)
        self.building.refresh_from_db()
        self.assertEqual(self.building.project_id, self.project.pk)

    def test_foreign_parent_and_parent_cycle_are_rejected(self):
        self.as_role(self.manager)
        self.grant('BuildingEditsAPIView', 'PATCH', self.manager)
        for parent in (self.foreign, self.building):
            response = self.api.patch(self.url('Building', f'Edits/{self.building.pk}/'), {'parent': parent.pk})
            self.assertEqual(response.status_code, 400)
        self.second.parent = self.building
        self.second.save()
        self.assertEqual(self.api.patch(self.url('Building', f'Edits/{self.building.pk}/'), {'parent': self.second.pk}).status_code, 400)

    def test_client_create_does_not_grant_management_links(self):
        self.grant('BuildingClientListCreateAPIView', 'POST')
        count = BuildingClient.objects.count()
        response = self.api.post(self.url('BuildingClient'), {'client': self.client.pk, 'building': self.other.pk})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(BuildingClient.objects.count(), count)

    def test_manager_create_binds_project_from_query(self):
        self.as_role(self.manager)
        self.grant('BuildingListCreateAPIView', 'POST', self.manager)
        response = self.api.post(self.url('Building'), {'code': 'NEW-MANAGED'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Building.objects.get(code='NEW-MANAGED').project_id, self.project.pk)

    def test_manager_cannot_link_asset_from_other_project(self):
        self.as_role(self.manager)
        self.grant('BuildingElevatorListCreateAPIView', 'POST', self.manager)
        count = BuildingElevator.objects.count()
        response = self.api.post(self.url('BuildingElevator'), {'building': self.building.pk, 'elevator': self.foreign_elevator.pk})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(BuildingElevator.objects.count(), count)

    def test_manager_cannot_link_user_without_project_membership(self):
        self.as_role(self.manager)
        self.grant('UserClientListCreateAPIView', 'POST', self.manager)
        response = self.api.post(self.url('UserClient'), {'client': self.client.pk, 'user': self.other_user.pk})
        self.assertEqual(response.status_code, 400)

    def test_part_installation_preserves_history_and_rejects_second_active_link(self):
        self.as_role(self.manager)
        self.grant('ProductElevatorListCreateAPIView', 'POST', self.manager)
        self.grant('ProductElevatorEditsAPIView', 'DELETE', self.manager)
        url = self.url('ProductElevator')
        self.assertEqual(self.api.post(url, {'product': self.part.pk,
                                             'elevator': self.other_elevator.pk}, format='json').status_code, 400)
        previous = ProductElevator.objects.get(product=self.part, elevator=self.elevator)
        removed = self.api.delete(self.url('ProductElevator', f'Edits/{previous.pk}/'))
        self.assertEqual(removed.status_code, 204)
        previous.refresh_from_db()
        self.assertFalse(previous.is_active)
        self.assertIsNotNone(previous.removed_at)
        self.assertEqual(previous.removed_by_id, self.user.pk)
        installed = self.api.post(url, {'product': self.part.pk, 'elevator': self.extra_elevator.pk},
                                  format='json')
        self.assertEqual(installed.status_code, 201, installed.data)
        current = ProductElevator.objects.get(pk=installed.data['id'])
        self.assertTrue(current.is_active)
        self.assertIsNotNone(current.installed_at)
        self.assertEqual(current.installed_by_id, self.user.pk)
        self.assertEqual(ProductElevator.objects.filter(product=self.part).count(), 2)
        self.assertEqual(self.api.post(url, {'product': self.part.pk, 'elevator': self.second_elevator.pk},
                                       format='json').status_code, 400)

    def test_active_part_installation_has_database_unique_constraint(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductElevator.objects.create(product=self.part, elevator=self.second_elevator, is_active=True)

    def test_none_scope_fails_closed_even_with_method_grant(self):
        self.role.asset_scope = 'none'
        self.role.save()
        self.grant('BuildingListCreateAPIView')
        self.assertEqual(self.api.get(self.url('Building')).data, [])

    def test_role_without_this_view_grant_cannot_expand_scope(self):
        RoleAssignment.objects.create(user=self.user, role=self.manager, project=self.project)
        self.grant('BuildingListCreateAPIView')
        response = self.api.get(self.url('Building'))
        self.assertEqual({row['id'] for row in response.data}, {self.building.pk, self.second.pk})

    def test_expert_nested_building_contains_only_selected_elevator(self):
        self.as_role(self.expert)
        visit = Visit.objects.create(type=self.visit_type, creator=self.other_user, expert=self.user,
                                     building=self.building)
        visit.elevator.add(self.elevator)
        self.grant('BuildingEditsAPIView', role=self.expert)
        response = self.api.get(self.url('Building', f'Edits/{self.building.pk}/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['elevator']['id'] for row in response.data['elevators']], [self.elevator.pk])
        self.assertEqual(self.api.get(self.url('Building', f'Edits/{self.other.pk}/')).status_code, 404)

    def test_legacy_expert_visit_uses_building_elevators(self):
        self.as_role(self.expert)
        Visit.objects.create(type=self.visit_type, creator=self.other_user, promoter=self.user, building=self.building)
        self.grant('ElevatorListCreateAPIView', role=self.expert)
        response = self.api.get(self.url('Elevator'))
        self.assertEqual({row['id'] for row in response.data}, {self.elevator.pk, self.extra_elevator.pk})

    def test_deleted_visit_does_not_grant_expert_access(self):
        self.as_role(self.expert)
        Visit.objects.create(type=self.visit_type, creator=self.other_user, expert=self.user,
                             building=self.building, is_deleted=True)
        self.grant('BuildingListCreateAPIView', role=self.expert)
        self.assertEqual(self.api.get(self.url('Building')).data, [])

    def test_supervisor_only_sees_active_team_assignments(self):
        self.as_role(self.supervisor)
        Supervisor.objects.create(supervisor=self.user, promoter=self.other_user, project=self.project)
        Visit.objects.create(type=self.visit_type, creator=self.user, expert=self.other_user, building=self.other)
        self.grant('BuildingListCreateAPIView', role=self.supervisor)
        self.assertEqual({row['id'] for row in self.api.get(self.url('Building')).data}, {self.other.pk})
        Supervisor.objects.filter(supervisor=self.user).update(is_active=False)
        self.assertEqual(self.api.get(self.url('Building')).data, [])

    def test_valid_request_creates_pending_visit_with_selected_assets(self):
        response = self.request()
        self.assertEqual(response.status_code, 201)
        visit = Visit.objects.get()
        self.assertEqual(visit.creator, self.user)
        self.assertEqual(visit.status, Visit.NOTVISITED)
        self.assertFalse(visit.is_active)
        self.assertEqual(list(visit.elevator.values_list('pk', flat=True)), [self.elevator.pk])
        self.assertEqual(ServiceRequestSubmission.objects.count(), 1)

    def test_entire_request_is_rejected_if_second_building_is_not_owned(self):
        response = self.request(rows=[
            {'building': self.building.pk, 'elevators': [self.elevator.pk]},
            {'building': self.other.pk, 'elevators': [self.other_elevator.pk]},
        ])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Visit.objects.count(), 0)
        self.assertEqual(ServiceRequestSubmission.objects.count(), 0)

    def test_invalid_elevator_and_foreign_project_request_are_rejected(self):
        for ids in ([self.other_elevator.pk], [self.foreign_elevator.pk], [999999]):
            response = self.request(rows=[{'building': self.building.pk, 'elevators': ids}])
            self.assertEqual(response.status_code, 400)
        foreign_type = VisitType.objects.create(title='Other type', project=self.foreign_project)
        self.assertEqual(self.request(type=foreign_type.pk).status_code, 400)
        self.assertEqual(Visit.objects.count(), 0)

    def test_inactive_visit_type_is_rejected(self):
        self.visit_type.is_active = False
        self.visit_type.save()
        self.assertEqual(self.request().status_code, 400)

    def test_duplicate_or_empty_selection_is_rejected(self):
        for rows in (
            [], [{'building': self.building.pk, 'elevators': []}],
            [{'building': self.building.pk, 'elevators': [self.elevator.pk, self.elevator.pk]}],
            [{'building': self.building.pk, 'elevators': [self.elevator.pk]}] * 2,
        ):
            self.assertEqual(self.request(buildings=rows).status_code, 400)
        self.assertEqual(Visit.objects.count(), 0)

    def test_retry_does_not_duplicate_visits(self):
        key = str(uuid.uuid4())
        first = self.request(request_key=key)
        second = self.request(request_key=key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['replayed'])
        self.assertEqual(first.data['successfuls'][0]['id'], second.data['successfuls'][0]['id'])
        self.assertEqual(Visit.objects.count(), 1)

    def test_reusing_key_with_different_payload_is_rejected(self):
        key = str(uuid.uuid4())
        self.assertEqual(self.request(request_key=key).status_code, 201)
        response = self.request(request_key=key, rows=[{'building': self.second.pk, 'elevators': [self.second_elevator.pk]}])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Visit.objects.count(), 1)

    def test_reordered_multi_building_retry_is_equivalent(self):
        key = str(uuid.uuid4())
        rows = [{'building': self.building.pk, 'elevators': [self.elevator.pk, self.extra_elevator.pk]},
                {'building': self.second.pk, 'elevators': [self.second_elevator.pk]}]
        self.assertEqual(self.request(rows=rows, request_key=key).status_code, 201)
        rows[0]['elevators'].reverse()
        self.assertEqual(self.request(rows=list(reversed(rows)), request_key=key).status_code, 200)
        self.assertEqual(Visit.objects.count(), 2)

    def test_creation_failure_rolls_back_all_records(self):
        rows = [{'building': self.building.pk, 'elevators': [self.elevator.pk]},
                {'building': self.second.pk, 'elevators': [self.second_elevator.pk]}]
        original = Visit.objects.create
        def fail_second(**kwargs):
            if kwargs['building_id'] == self.second.pk:
                raise RuntimeError('Simulated local persistence failure')
            return original(**kwargs)
        with patch('visit.service_requests.Visit.objects.create', side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.request(rows=rows)
        self.assertEqual(Visit.objects.count(), 0)
        self.assertEqual(ServiceRequestSubmission.objects.count(), 0)

    def test_request_requires_explicit_role_grant(self):
        response = self.api.post(f'/core/api/service_request/create/?p={self.project.pk}', {
            'type': self.visit_type.pk, 'buildings': [{'building': self.building.pk, 'elevators': [self.elevator.pk]}],
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_client_visits_include_pending_overdue_future_and_history(self):
        self.grant('ClientVisitsAPIView')
        ids = []
        for days, status in ((-5, '0'), (5, '0'), (0, '3')):
            visit = Visit.objects.create(type=self.visit_type, creator=self.user, building=self.building,
                                         has_due_date=True, due_date=timezone.localdate() + timedelta(days=days),
                                         status=status, is_active=False)
            ids.append(visit.pk)
        Visit.objects.create(type=self.visit_type, creator=self.other_user, building=self.other)
        response = self.api.get(f'/core/api/client/open_visits/list/?p={self.project.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.data}, set(ids))

    def test_client_dashboard_requires_both_get_grants_and_is_scoped(self):
        url = f'/core/api/client/dashboard/?p={self.project.pk}'
        self.assertEqual(self.api.get(url).status_code, 403)
        self.grant('BuildingClientListCreateAPIView')
        self.assertEqual(self.api.get(url).status_code, 403)
        self.grant('ClientVisitsAPIView')
        own = Visit.objects.create(type=self.visit_type, creator=self.user, building=self.building,
                                   has_due_date=True, due_date=timezone.localdate() + timedelta(days=2),
                                   status=Visit.NOTVISITED, is_active=True)
        Visit.objects.create(type=self.visit_type, creator=self.other_user, building=self.other,
                             status=Visit.NOTVISITED, is_active=True)
        result = self.api.get(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['counts']['buildings'], 2)
        self.assertEqual(result.data['counts']['elevators'], 3)
        self.assertEqual(result.data['counts']['active'], 1)
        self.assertEqual(result.data['next_visit']['id'], own.pk)
        self.assertEqual({row['id'] for row in result.data['buildings']},
                         {self.building.pk, self.second.pk})
        self.assertEqual({row['id'] for row in result.data['recent_visits']}, {own.pk})
        self.assertEqual(self.api.get(f'/core/api/client/dashboard/?p={self.foreign_project.pk}').status_code, 403)

    def test_client_dashboard_splits_pending_active_and_overdue(self):
        self.grant('BuildingClientListCreateAPIView')
        self.grant('ClientVisitsAPIView')
        self.request()
        Visit.objects.create(type=self.visit_type, creator=self.user, building=self.second,
                             has_due_date=True, due_date=timezone.localdate() - timedelta(days=1),
                             status=Visit.NOTVISITED, is_active=True)
        result = self.api.get(f'/core/api/client/dashboard/?p={self.project.pk}')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['counts']['pending'], 1)
        self.assertEqual(result.data['counts']['active'], 1)
        self.assertEqual(result.data['counts']['overdue'], 1)
        self.assertIsNone(result.data['next_visit'])

    def test_expert_queue_includes_owned_overdue_and_future_visits(self):
        self.as_role(self.expert)
        self.grant('PromoterVisitsAPIView', role=self.expert)
        today = timezone.localdate()
        overdue = Visit.objects.create(type=self.visit_type, creator=self.other_user,
                                       building=self.building, expert=self.user,
                                       has_due_date=True, due_date=today - timedelta(days=1), is_active=True)
        future = Visit.objects.create(type=self.visit_type, creator=self.other_user,
                                      building=self.second, promoter=self.user,
                                      has_due_date=True, due_date=today + timedelta(days=2), is_active=True)
        Visit.objects.create(type=self.visit_type, creator=self.other_user,
                             building=self.other, promoter=self.other_user, is_active=True)
        base = f'/core/api/promoter/open_visits/list/?p={self.project.pk}'
        response = self.api.get(base)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.data}, {overdue.pk, future.pk})
        self.assertEqual({row['id'] for row in self.api.get(base + '&schedule=overdue').data}, {overdue.pk})
        self.assertEqual({row['id'] for row in self.api.get(base + '&schedule=upcoming').data}, {future.pk})

    def test_admin_action_plan_creates_all_valid_rows_and_reports_invalid_ones(self):
        self.as_role(self.manager)
        self.grant('AdminActionPlanCreate', 'POST', role=self.manager)
        RoleAssignment.objects.create(user=self.other_user, role=self.expert, project=self.project)
        url = f'/core/api/admin/action_plan/create/?p={self.project.pk}'
        payload = {
            'project': self.project.pk, 'visit_type': self.visit_type.pk,
            'has_due_date': False, 'due_date': None,
            'actions': [
                {'building_code': self.building.code, 'expert_phone_number': self.other_user.username,
                 'elevator_ids': [self.elevator.pk]},
                {'building_code': self.second.code, 'expert_phone_number': self.other_user.username,
                 'elevator_ids': [self.second_elevator.pk]},
                {'building_code': self.foreign.code, 'expert_phone_number': self.other_user.username},
                {'building_code': self.building.code, 'expert_phone_number': self.other_user.username,
                 'elevator_ids': [self.other_elevator.pk]},
            ],
        }
        response = self.api.post(url, payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['successfuls']), 2)
        self.assertEqual([error['index'] for error in response.data['errors']], [2, 3])
        self.assertEqual(Visit.objects.get(building=self.building,
                                           creator=self.user).elevator.get().pk, self.elevator.pk)
        self.assertEqual(Visit.objects.filter(creator=self.user, expert=self.other_user,
                                              type=self.visit_type).count(), 2)
        self.assertFalse(Visit.objects.filter(creator=self.user, expert=self.other_user,
                                              is_active=True).exists())
        payload['project'] = self.foreign_project.pk
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 400)

    def test_action_plan_edit_cannot_bypass_visit_workflow_or_delete_completed_work(self):
        self.as_role(self.manager)
        self.grant('AdminActionPlanEdits', 'PATCH', self.manager)
        self.grant('AdminActionPlanEdits', 'DELETE', self.manager)
        visit = Visit.objects.create(creator=self.user, type=self.visit_type,
                                     building=self.building)
        url = f'/core/api/admin/action_plan/edits/{visit.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.patch(url, {'status': Visit.APPROVED}, format='json').status_code, 405)
        visit.refresh_from_db()
        self.assertEqual(visit.status, Visit.NOTVISITED)
        visit.status = Visit.COMPLETED
        visit.save()
        self.assertEqual(self.api.delete(url).status_code, 400)
        visit.refresh_from_db()
        self.assertFalse(visit.is_deleted)
        visit.status = Visit.NOTVISITED
        visit.save()
        self.assertEqual(self.api.delete(url).status_code, 204)
        visit.refresh_from_db()
        self.assertTrue(visit.is_deleted)

    def test_action_plan_me_filter_uses_creator_and_project(self):
        self.as_role(self.manager)
        self.grant('AdminActionPlanList', 'GET', self.manager)
        own = Visit.objects.create(creator=self.user, type=self.visit_type,
                                   building=self.building)
        Visit.objects.create(creator=self.other_user, type=self.visit_type,
                             building=self.second)
        foreign_type = VisitType.objects.create(project=self.foreign_project)
        Visit.objects.create(creator=self.user, type=foreign_type, building=self.foreign)
        response = self.api.get(f'/core/api/admin/action_plan/list/?p={self.project.pk}&me=true')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual({row['id'] for row in response.data}, {own.pk})

    def test_pagination_retains_asset_scope(self):
        self.grant('BuildingListCreateAPIView')
        response = self.api.get(self.url('Building') + '&limit=1&offset=1&ordering=id')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], self.second.pk)

    def test_navigation_uses_active_project_memberships_and_grants(self):
        self.grant('NavMenuList')
        own = NavMenu.objects.create(role=self.role, route='home')
        global_menu = NavMenu.objects.create(role=None, route='setting')
        NavMenu.objects.create(role=self.manager, route='tasks')
        RoleAssignment.objects.create(user=self.user, role=self.manager, project=self.foreign_project)
        response = self.api.get(f'/config/navbar/List/?p={self.project.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.data}, {own.pk, global_menu.pk})
        RoleAssignment.objects.filter(user=self.user, project=self.project).update(is_deleted=True)
        self.assertEqual(self.api.get(f'/config/navbar/List/?p={self.project.pk}').status_code, 403)

    def test_project_cannot_be_cleared_via_asset_api(self):
        self.as_role(self.manager)
        self.grant('BuildingEditsAPIView', 'PATCH', role=self.manager)
        response = self.api.patch(self.url('Building', f'Edits/{self.building.pk}/'), {'project': None}, format='json')
        self.assertEqual(response.status_code, 400)
        self.building.refresh_from_db()
        self.assertEqual(self.building.project_id, self.project.pk)

    def test_finished_inactive_visit_is_not_a_pending_request(self):
        response = self.request()
        visit = Visit.objects.get(pk=response.data['successfuls'][0]['id'])
        self.grant('ClientVisitsAPIView')
        pending = self.api.get(f'/core/api/client/open_visits/list/?p={self.project.pk}')
        self.assertTrue(pending.data[0]['is_pending_request'])
        visit.status = Visit.COMPLETED
        visit.save()
        history = self.api.get(f'/core/api/client/open_visits/list/?p={self.project.pk}')
        self.assertFalse(history.data[0]['is_pending_request'])

    def test_navigation_excludes_ungranted_role_in_same_project(self):
        self.grant('NavMenuList')
        own = NavMenu.objects.create(role=self.role, route='home')
        NavMenu.objects.create(role=self.manager, route='tasks')
        RoleAssignment.objects.create(user=self.user, role=self.manager, project=self.project)
        response = self.api.get(f'/config/navbar/List/?p={self.project.pk}')
        self.assertEqual({row['id'] for row in response.data}, {own.pk})

    def test_self_memberships_exclude_deleted_inactive_and_other_users(self):
        RoleAssignment.objects.create(user=self.other_user, role=self.role, project=self.project)
        self.foreign_project.is_active = False
        self.foreign_project.save()
        RoleAssignment.objects.create(user=self.user, role=self.role, project=self.foreign_project)
        RoleAssignment.objects.create(user=self.user, role=self.manager, project=self.project, is_deleted=True)
        response = self.api.get('/core/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['role']['id'], self.role.pk)

    def test_building_search_retains_ownership(self):
        self.grant('BuildingClientListCreateAPIView')
        self.building.verbose_name = 'Find this building'
        self.building.save()
        self.other.verbose_name = 'Find this forbidden'
        self.other.save()
        response = self.api.get(f'/api/visit/BuildingClientListCreate/?p={self.project.pk}&search=Find&limit=1')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['building']['id'], self.building.pk)


    def field_question_setup(self):
        self.as_role(self.expert)
        self.grant('QuestionListForVisitsAPIView', role=self.expert)
        self.grant('PromoterAnswersQuestionsView', 'POST', role=self.expert)
        question_type = QuestionType.objects.create(
            name='Safety', project=self.project, visit_type=self.visit_type,
        )
        question = Question.objects.create(
            type=Question.TGENERAL, question_type=question_type, text='Safe?',
        )
        for field in ('bool', 'number', 'multichoice'):
            question.answer_type.add(AnswerType.objects.create(name=field, field=field))
        choice = AnswerChoice.objects.create(answer='Allowed', question=question)
        question.answer_choices.add(choice)
        visit = Visit.objects.create(
            creator=self.user, expert=self.user, promoter=self.user,
            type=self.visit_type, building=self.building, is_active=True,
        )
        return question, choice, visit

    def test_field_questions_require_assigned_visit_and_project(self):
        question, _, visit = self.field_question_setup()
        url = f'/core/api/promoter/questions/list/visit/{visit.pk}/?p={self.project.pk}'
        response = self.api.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['question']['id'] for row in response.data], [question.pk])
        self.assertEqual(self.api.get(url.replace(f'p={self.project.pk}', f'p={self.foreign_project.pk}')).status_code, 403)
        other = Visit.objects.create(
            creator=self.other_user, expert=self.other_user, promoter=self.other_user,
            type=self.visit_type, building=self.other, is_active=True,
        )
        self.assertEqual(self.api.get(f'/core/api/promoter/questions/list/visit/{other.pk}/?p={self.project.pk}').status_code, 404)

    def test_field_answer_rejects_mass_assignment_foreign_choices_and_closed_visit(self):
        question, choice, visit = self.field_question_setup()
        url = f'/core/api/promoter/answer_to_question/?p={self.project.pk}'
        payload = {'visit': visit.pk, 'question': question.pk, 'bool': False}
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 200)
        self.assertIs(Answer.objects.get(visit=visit, question=question).bool, False)
        self.assertEqual(self.api.post(url, {**payload, 'number': 0}, format='json').status_code, 200)
        self.assertEqual(Answer.objects.filter(visit=visit, question=question).count(), 1)
        self.assertEqual(Answer.objects.get(visit=visit, question=question).number, 0)
        self.assertEqual(self.api.post(url, {**payload, 'datetime_created': '2000-01-01'}, format='json').status_code, 400)
        foreign_choice = AnswerChoice.objects.create(answer='Forbidden')
        self.assertEqual(self.api.post(url, {'visit': visit.pk, 'question': question.pk,
                                             'multichoice': [choice.pk, foreign_choice.pk]}, format='json').status_code, 400)
        other = Visit.objects.create(
            creator=self.other_user, expert=self.other_user, promoter=self.other_user,
            type=self.visit_type, building=self.other, is_active=True,
        )
        self.assertEqual(self.api.post(url, {**payload, 'visit': other.pk}, format='json').status_code, 404)
        visit.status = Visit.APPROVED
        visit.save()
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 404)

    def test_image_upload_validates_assignment_type_and_file_before_storage(self):
        from PIL import Image
        _, _, visit = self.field_question_setup()
        self.grant('PromoterUploadImageAPIView', 'POST', role=self.expert)
        photo_type = PhotoType.objects.create(name='StoreFront', project=self.project, visit_type=self.visit_type)
        foreign_type = PhotoType.objects.create(name='Foreign', project=self.foreign_project)
        other = Visit.objects.create(
            creator=self.other_user, expert=self.other_user, promoter=self.other_user,
            type=self.visit_type, building=self.other, is_active=True,
        )
        buffer = BytesIO()
        Image.new('RGB', (2, 2), 'blue').save(buffer, format='PNG')

        def upload(visit_id, type_id, content=None):
            content = buffer.getvalue() if content is None else content
            return self.api.post(f'/core/api/promoter/open_visit/upload_image/?p={self.project.pk}', {
                'visit': visit_id, 'type': type_id,
                'link': SimpleUploadedFile('photo.png', content, content_type='image/png'),
            }, format='multipart')

        with patch('visit.views.ArvanStorage') as storage:
            storage.return_value.put_file.return_value = 'https://example.invalid/photo.png'
            self.assertEqual(upload(other.pk, photo_type.pk).status_code, 404)
            self.assertEqual(upload(visit.pk, foreign_type.pk).status_code, 404)
            self.assertEqual(upload(visit.pk, photo_type.pk, b'not-an-image').status_code, 400)
            storage.return_value.put_file.assert_not_called()
            response = upload(visit.pk, photo_type.pk)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(Photo.objects.filter(visit=visit, type=photo_type).count(), 1)
            storage.return_value.put_file.assert_called_once()

    def test_field_completion_requires_mandatory_answers_and_photos(self):
        question, _, visit = self.field_question_setup()
        self.grant('PromoterVisitStatusChangeAPIView', 'PUT', role=self.expert)
        question.is_mandatory = True
        question.save()
        photo_type = PhotoType.objects.create(
            name='StoreFront', project=self.project, visit_type=self.visit_type, min=1,
        )
        url = f'/core/api/promoter/open_visit/change_status/{visit.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.put(url, {'status': Visit.INPROGRESS}, format='json').status_code, 200)
        self.building.refresh_from_db()
        self.assertTrue(self.building.is_visiting)
        blocked = self.api.put(url, {'status': Visit.COMPLETED}, format='json')
        self.assertEqual(blocked.status_code, 400)
        self.assertIn(question.pk, blocked.data['requirements']['questions'])
        self.assertEqual(blocked.data['requirements']['photo_types'][0]['type'], photo_type.pk)
        Answer.objects.create(visit=visit, question=question, bool=False)
        self.assertEqual(self.api.put(url, {'status': Visit.COMPLETED}, format='json').status_code, 400)
        Photo.objects.create(visit=visit, type=photo_type, creator=self.user, link='https://example.invalid/photo.png')
        self.assertEqual(self.api.put(url, {'status': Visit.COMPLETED}, format='json').status_code, 200)
        snapshot = VisitReportSnapshot.objects.get(visit=visit, version=1)
        self.assertIs(snapshot.payload['answers'][0]['bool'], False)
        answer = Answer.objects.get(visit=visit, question=question)
        answer.bool = True
        answer.save()
        snapshot.refresh_from_db()
        self.assertIs(snapshot.payload['answers'][0]['bool'], False)
        from visit.report_snapshot import capture_report_snapshot
        self.assertEqual(capture_report_snapshot(visit, self.user).pk, snapshot.pk)
        self.assertEqual(VisitReportSnapshot.objects.filter(visit=visit).count(), 1)
        self.assertEqual(self.api.put(url, {'status': Visit.INPROGRESS}, format='json').status_code, 400)
        self.building.refresh_from_db()
        self.assertFalse(self.building.is_visiting)

    def test_visit_page_settings_progress_is_not_complete_without_answers(self):
        question, _, visit = self.field_question_setup()
        self.grant('FrontVisitPageSettingsView', role=self.expert)
        url = f'/core/api/promoter/visit_page_settings/{visit.pk}/?p={self.project.pk}'
        first = self.api.get(url)
        self.assertEqual(first.status_code, 200, first.data)
        self.assertFalse(first.data['questions'][0]['status'])
        self.assertEqual(first.data['questions'][0]['progress'], '0%')
        Answer.objects.create(visit=visit, question=question, bool=False)
        second = self.api.get(url)
        self.assertTrue(second.data['questions'][0]['status'])
        other = Visit.objects.create(
            creator=self.other_user, expert=self.other_user, promoter=self.other_user,
            type=self.visit_type, building=self.other, is_active=True,
        )
        self.assertEqual(self.api.get(f'/core/api/promoter/visit_page_settings/{other.pk}/?p={self.project.pk}').status_code, 404)

    def test_management_transfer_preserves_old_reports_without_current_asset_access(self):
        self.grant('BuildingClientListCreateAPIView')
        self.grant('ClientVisitsAPIView')
        closed = Visit.objects.create(
            creator=self.user, type=self.visit_type, building=self.building,
            status=Visit.COMPLETED, is_active=True,
        )
        current = Visit.objects.create(
            creator=self.user, type=self.visit_type, building=self.building,
            status=Visit.INPROGRESS, is_active=True,
        )
        old_link = BuildingClient.objects.get(building=self.building, client=self.client)
        old_link.end_at = timezone.now()
        old_link.save()
        BuildingClient.objects.create(building=self.building, client=self.other_client)
        old_buildings = self.api.get(self.url('BuildingClient'))
        self.assertEqual({row['building']['id'] for row in old_buildings.data}, {self.second.pk})
        old_visits = self.api.get(f'/core/api/client/open_visits/list/?p={self.project.pk}')
        self.assertEqual({row['id'] for row in old_visits.data}, {closed.pk})

        RoleAssignment.objects.create(user=self.other_user, role=self.role, project=self.project)
        self.api.force_authenticate(self.other_user)
        new_buildings = self.api.get(self.url('BuildingClient'))
        self.assertEqual({row['building']['id'] for row in new_buildings.data}, {self.building.pk, self.other.pk})
        new_visits = self.api.get(f'/core/api/client/open_visits/list/?p={self.project.pk}')
        self.assertIn(current.pk, {row['id'] for row in new_visits.data})
        self.assertNotIn(closed.pk, {row['id'] for row in new_visits.data})

    def test_visit_detail_and_photo_history_follow_project_and_person_scope(self):
        own = Visit.objects.create(creator=self.user, type=self.visit_type, building=self.building)
        other = Visit.objects.create(creator=self.other_user, type=self.visit_type, building=self.other)
        foreign_type = VisitType.objects.create(project=self.foreign_project)
        foreign = Visit.objects.create(creator=self.other_user, type=foreign_type, building=self.foreign)
        photo_type = PhotoType.objects.create(name='Evidence', project=self.project, visit_type=self.visit_type)
        for visit in (own, other):
            Photo.objects.create(visit=visit, type=photo_type, link='https://example.invalid/photo.png')
        detail = f'/core/api/visit/retrieve/{own.pk}/?p={self.project.pk}'
        history = f'/core/api/promoter/visit/photo_history/?p={self.project.pk}'
        self.assertEqual(self.api.get(detail).status_code, 403)
        self.grant('VisitDetailRetriveAPIView')
        self.grant('ListPhotoForVisitView')
        self.assertEqual(self.api.get(detail).status_code, 200)
        self.assertEqual(self.api.get(detail.replace(str(own.pk) + '/', str(other.pk) + '/')).status_code, 404)
        self.assertEqual(self.api.get(detail.replace(str(own.pk) + '/', str(foreign.pk) + '/')).status_code, 404)
        self.assertEqual({row['visit'] for row in self.api.get(history).data}, {own.pk})

        self.as_role(self.expert)
        self.grant('VisitDetailRetriveAPIView', role=self.expert)
        self.assertEqual(self.api.get(detail).status_code, 404)
        own.expert = self.user
        own.save()
        self.assertEqual(self.api.get(detail).status_code, 200)

    def test_batch_mutations_validate_every_id_and_project_before_update(self):
        own = Visit.objects.create(creator=self.user, type=self.visit_type, building=self.building)
        foreign_type = VisitType.objects.create(project=self.foreign_project)
        foreign = Visit.objects.create(creator=self.user, type=foreign_type, building=self.foreign)
        url = f'/core/api/admin/action_plan/bulk_update/?p={self.project.pk}'
        payload = {'id': [own.pk, foreign.pk], 'is_active': True, 'is_deleted': False}
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 403)
        self.as_role(self.manager)
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 403)
        self.grant('AdminActionPlanBulkEdits', 'POST', self.manager)
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 400)
        own.refresh_from_db()
        self.assertFalse(own.is_active)
        self.assertEqual(self.api.post(url, {**payload, 'id': [own.pk]}, format='json').status_code, 200)
        own.refresh_from_db()
        self.assertTrue(own.is_active)
        self.assertEqual(self.api.post(url, {**payload, 'id': [own.pk, own.pk]}, format='json').status_code, 400)

    def test_legacy_visit_batch_requires_grant_and_project_scope(self):
        RoleAssignment.objects.create(user=self.other_user, role=self.expert, project=self.project)
        own = Visit.objects.create(creator=self.user, type=self.visit_type, building=self.building,
                                   expert=self.other_user, promoter=self.other_user)
        url = f'/core/api/v1/visit_activation_edit/?p={self.project.pk}'
        payload = {'ids': [own.pk], 'is_active': True, 'is_deleted': False}
        self.api.force_authenticate(user=None)
        self.assertIn(self.api.post(url, payload, format='json').status_code, (401, 403))
        self.api.force_authenticate(self.user)
        self.grant('VisitBulkEditsView', 'POST')
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 403)
        self.as_role(self.manager)
        self.grant('VisitBulkEditsView', 'POST', self.manager)
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 200)
        own.refresh_from_db()
        self.assertTrue(own.is_active)
        self.assertEqual(InAppNotification.objects.filter(
            recipient=self.other_user, kind='visit_assignment', object_id=own.pk).count(), 1)

    def test_supervisor_can_dispatch_only_to_active_subordinates(self):
        self.as_role(self.supervisor)
        self.grant('AdminActionPlanCreate', 'POST', self.supervisor)
        self.grant('AdminActionPlanBulkEdits', 'POST', self.supervisor)
        RoleAssignment.objects.create(user=self.other_user, role=self.expert, project=self.project)
        url = f'/core/api/admin/action_plan/create/?p={self.project.pk}'
        payload = {'project': self.project.pk, 'visit_type': self.visit_type.pk,
                   'has_due_date': False, 'due_date': None,
                   'actions': [{'building_code': self.building.code,
                                'expert_phone_number': self.other_user.username}]}
        refused = self.api.post(url, payload, format='json')
        self.assertEqual(refused.status_code, 200)
        self.assertEqual(len(refused.data['errors']), 1)
        self.assertEqual(Visit.objects.count(), 0)
        Supervisor.objects.create(supervisor=self.user, promoter=self.other_user,
                                  project=self.project, is_active=True)
        created = self.api.post(url, payload, format='json')
        self.assertEqual(created.status_code, 200, created.data)
        self.assertEqual(len(created.data['successfuls']), 1)
        visit_id = created.data['successfuls'][0]['id']
        self.assertFalse(InAppNotification.objects.filter(recipient=self.other_user).exists())
        active = self.api.post(f'/core/api/admin/action_plan/bulk_update/?p={self.project.pk}',
                               {'id': [visit_id], 'is_active': True}, format='json')
        self.assertEqual(active.status_code, 200, active.data)
        self.assertTrue(Visit.objects.get(pk=visit_id).is_active)
        self.assertEqual(InAppNotification.objects.filter(
            recipient=self.other_user, kind='visit_assignment', object_id=visit_id).count(), 1)
        self.assertEqual(self.api.post(f'/core/api/admin/action_plan/bulk_update/?p={self.project.pk}',
                                       {'id': [visit_id], 'is_active': True}, format='json').status_code, 200)
        self.assertEqual(InAppNotification.objects.filter(recipient=self.other_user).count(), 1)
        direct = self.api.post(url, {**payload, 'actions': [{
            **payload['actions'][0], 'is_active': True,
        }]}, format='json')
        self.assertEqual(direct.status_code, 200, direct.data)
        self.assertEqual(InAppNotification.objects.filter(recipient=self.other_user).count(), 2)

    def test_photo_delete_and_location_batch_cannot_cross_projects(self):
        own = Visit.objects.create(creator=self.user, promoter=self.user,
                                   type=self.visit_type, building=self.building)
        foreign_type = VisitType.objects.create(project=self.foreign_project)
        foreign = Visit.objects.create(creator=self.user, promoter=self.user,
                                       type=foreign_type, building=self.foreign)
        own_type = PhotoType.objects.create(name='Owned evidence', project=self.project, visit_type=self.visit_type)
        other_type = PhotoType.objects.create(name='Foreign evidence', project=self.foreign_project,
                                              visit_type=foreign_type)
        own_photo = Photo.objects.create(visit=own, type=own_type)
        foreign_photo = Photo.objects.create(visit=foreign, type=other_type)
        self.as_role(self.expert)
        self.grant('PromoterDeletePhotoView', 'DELETE', self.expert)
        delete = f'/core/api/promoter/visit/delete_photo/{foreign_photo.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.delete(delete).status_code, 404)
        self.assertFalse(Photo.objects.get(pk=foreign_photo.pk).is_deleted)
        self.as_role(self.manager)
        self.grant('VisitChangePhotoLocations', 'POST', self.manager)
        location = f'/core/api/admin/visit/change_photo_location/?p={self.project.pk}'
        payload = {'ids': [own_photo.pk, foreign_photo.pk], 'longitude': '51', 'latitude': '35'}
        self.assertEqual(self.api.post(location, payload, format='json').status_code, 400)
        self.assertIsNone(Photo.objects.get(pk=own_photo.pk).latitude)
        self.assertEqual(self.api.post(location, {**payload, 'ids': [own_photo.pk]}, format='json').status_code, 200)
        self.assertEqual(str(Photo.objects.get(pk=own_photo.pk).latitude), '35.0000000000000000')

    def test_ticket_conversation_stays_with_project_and_participant(self):
        self.grant('TicketListCreateView')
        self.grant('TicketListCreateView', 'POST')
        self.grant('TicketMessageListCreateView')
        self.grant('TicketMessageListCreateView', 'POST')
        ticket_url = f'/core/api/admin/ticket/list_create/?p={self.project.pk}'
        message_url = f'/core/api/admin/ticket_message/list_create/?p={self.project.pk}'
        self.assertEqual(self.api.post(ticket_url, {'project': self.foreign_project.pk,
                                                    'role_assignee': self.role.pk, 'title': 'Wrong project'},
                                       format='json').status_code, 400)
        own = self.api.post(ticket_url, {'project': self.project.pk,
                                          'role_assignee': self.role.pk, 'title': 'Support',
                                          'building': self.building.pk}, format='json')
        self.assertEqual(own.status_code, 201, own.data)
        own_ticket = Ticket.objects.get(pk=own.data['id'])
        self.assertEqual(own_ticket.project_id, self.project.pk)
        self.assertEqual(own_ticket.creator_id, self.user.pk)
        self.assertEqual(own_ticket.status, Ticket.WAITING)
        other = Ticket.objects.create(project=self.project, creator=self.other_user,
                                      role_assignee=self.role, title='Private')
        self.assertEqual({row['id'] for row in self.api.get(ticket_url).data}, {own_ticket.pk})
        self.assertEqual(self.api.post(message_url, {'ticket': other.pk, 'body': 'Forbidden'},
                                       format='json').status_code, 403)
        self.assertEqual(self.api.post(message_url, {'ticket': own_ticket.pk, 'body': 'Hello'},
                                       format='json').status_code, 201)
        self.assertEqual({row['ticket']['id'] for row in self.api.get(message_url).data},
                         {own_ticket.pk})
        self.assertEqual(TicketMessage.objects.count(), 1)
        self.grant('TicketRetriveUpdateDestroyView')
        self.grant('TicketRetriveUpdateDestroyView', 'PATCH')
        self.assertEqual(self.api.get(f'/core/api/admin/ticket/edits/{other.pk}/?p={self.project.pk}').status_code, 404)
        self.assertEqual(self.api.patch(f'/core/api/admin/ticket/edits/{other.pk}/?p={self.project.pk}',
                                        {'status': Ticket.CLOSED}, format='json').status_code, 404)
        self.assertEqual(self.api.patch(f'/core/api/admin/ticket/edits/{own_ticket.pk}/?p={self.project.pk}',
                                        {'project': self.foreign_project.pk, 'status': Ticket.CLOSED},
                                        format='json').status_code, 200)
        own_ticket.refresh_from_db()
        self.assertEqual(own_ticket.project_id, self.project.pk)
        self.assertEqual(own_ticket.status, Ticket.CLOSED)
        self.assertEqual(self.api.post(message_url, {'ticket': own_ticket.pk, 'body': 'Late'},
                                       format='json').status_code, 400)

    def test_ticket_attachment_upload_validates_message_and_file_before_storage(self):
        self.grant('TicketUploadAttachmentAPIView', 'POST')
        ticket = Ticket.objects.create(project=self.project, creator=self.user, role_assignee=self.role)
        message = TicketMessage.objects.create(ticket=ticket, created_by=self.user, body='Evidence')
        other = Ticket.objects.create(project=self.project, creator=self.other_user, role_assignee=self.role)
        foreign_message = TicketMessage.objects.create(ticket=other, created_by=self.other_user, body='Private')
        url = f'/core/api/admin/ticket_message_attachment/upload/?p={self.project.pk}'
        with patch('visit.views.ArvanStorage.put_file', return_value='https://example.invalid/evidence.pdf') as store:
            denied = self.api.post(url, {'ticket_message': foreign_message.pk,
                                         'link': SimpleUploadedFile('evidence.pdf', b'%PDF-1.7\n')})
            self.assertEqual(denied.status_code, 403)
            invalid = self.api.post(url, {'ticket_message': message.pk,
                                          'link': SimpleUploadedFile('bad.pdf', b'not a pdf')})
            self.assertEqual(invalid.status_code, 400)
            store.assert_not_called()
            accepted = self.api.post(url, {'ticket_message': message.pk,
                                           'link': SimpleUploadedFile('evidence.pdf', b'%PDF-1.7\n')})
            self.assertEqual(accepted.status_code, 201, accepted.data)
            store.assert_called_once()
        self.assertEqual(TicketMessageAttachment.objects.get().ticket_message_id, message.pk)

    def test_field_permission_rejects_json_patch_and_combines_authorized_roles(self):
        ticket = Ticket.objects.create(project=self.project, creator=self.user, role_assignee=self.role)
        url = f'/core/api/admin/ticket/edits/{ticket.pk}/?p={self.project.pk}'
        grant = self.grant('TicketRetriveUpdateDestroyView', 'PATCH')
        field = ModelField.objects.create(model_name='Ticket', field_name='status', field_type='CharField')
        RoleViewModelField.objects.create(role_view=grant, model_field=field, can_update=False)
        self.assertEqual(self.api.patch(url, {'status': Ticket.CLOSED}, format='json').status_code, 403)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.WAITING)
        RoleAssignment.objects.create(user=self.user, role=self.manager, project=self.project)
        self.grant('TicketRetriveUpdateDestroyView', 'PATCH', self.manager)
        self.assertEqual(self.api.patch(url, {'status': Ticket.CLOSED}, format='json').status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.CLOSED)

    def test_project_admin_delete_ends_management_without_deleting_history(self):
        link = BuildingClient.objects.get(building=self.building, client=self.client)
        self.as_role(self.manager)
        self.grant('BuildingClientEditsAPIView', 'DELETE', role=self.manager)
        response = self.api.delete(self.url('BuildingClient', f'Edits/{link.pk}/'))
        self.assertEqual(response.status_code, 204)
        link.refresh_from_db()
        self.assertIsNotNone(link.end_at)
        self.assertTrue(BuildingClient.objects.filter(pk=link.pk).exists())

    def test_transfer_management_is_atomic_scoped_and_repeatable(self):
        old_link = BuildingClient.objects.get(building=self.building, client=self.client)
        url = f'/core/api/admin/building_management/transfer/?p={self.project.pk}'
        payload = {'building': self.building.pk, 'client': self.other_client.pk,
                   'reason': 'مدیریت ساختمان واگذار شد'}
        self.grant('BuildingClientListCreateAPIView', 'POST')
        self.assertEqual(self.api.post(url, payload, format='json').status_code, 403)

        self.as_role(self.manager)
        self.grant('BuildingClientListCreateAPIView', 'POST', role=self.manager)
        foreign_client = Client.objects.create(project=self.foreign_project)
        self.assertEqual(self.api.post(url, {**payload, 'client': foreign_client.pk}, format='json').status_code, 404)
        self.assertIsNone(BuildingClient.objects.get(pk=old_link.pk).end_at)
        result = self.api.post(url, payload, format='json')
        self.assertEqual(result.status_code, 201, result.data)
        old_link.refresh_from_db()
        self.assertIsNotNone(old_link.end_at)
        self.assertEqual(old_link.ended_by_id, self.user.pk)
        self.assertEqual(old_link.end_reason, payload['reason'])
        new_link = BuildingClient.objects.get(pk=result.data['management_id'])
        self.assertEqual(new_link.client_id, self.other_client.pk)
        self.assertEqual(new_link.started_by_id, self.user.pk)
        self.assertEqual(new_link.start_reason, payload['reason'])
        replay = self.api.post(url, payload, format='json')
        self.assertEqual(replay.status_code, 200)
        self.assertFalse(replay.data['changed'])
        self.assertEqual(BuildingClient.objects.filter(building=self.building).count(), 2)

    def test_client_visit_types_accept_only_types_from_selected_project(self):
        self.as_role(self.manager)
        self.grant('ClientListCreateAPIView', 'POST', role=self.manager)
        url = self.url('Client')
        response = self.api.post(url, {'name': 'New client', 'visit_types': [self.visit_type.pk]}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        created = Client.objects.get(pk=response.data['id'])
        self.assertEqual(list(created.visit_types.values_list('pk', flat=True)), [self.visit_type.pk])
        self.assertNotIn('legacy_visits', response.data)
        foreign_type = VisitType.objects.create(project=self.foreign_project)
        self.assertEqual(self.api.post(url, {'name': 'Bad client', 'visit_types': [foreign_type.pk]}, format='json').status_code, 400)


class LegacyAssetAssignmentTests(TestCase):
    def test_legacy_client_visit_links_copy_valid_types_without_losing_source(self):
        import importlib
        from django.apps import apps
        from django.db import connection
        from types import SimpleNamespace

        migration = importlib.import_module('visit.migrations.0092_client_visit_type_relation')
        project = Project.objects.create(name='A')
        other = Project.objects.create(name='B')
        user = User.objects.create(username='legacy-type-user')
        building = Building.objects.create(project=project)
        client = Client.objects.create(project=project)
        matching_type = VisitType.objects.create(project=project)
        foreign_type = VisitType.objects.create(project=other)
        matching = Visit.objects.create(creator=user, building=building, type=matching_type)
        foreign = Visit.objects.create(creator=user, building=building, type=foreign_type)
        client.legacy_visits.add(matching, foreign)
        migration.copy_legacy_visit_types(apps, SimpleNamespace(connection=connection))
        self.assertEqual(list(client.visit_types.values_list('pk', flat=True)), [matching_type.pk])
        self.assertEqual(set(client.legacy_visits.values_list('pk', flat=True)), {matching.pk, foreign.pk})

    def migrate_data(self):
        import importlib
        from django.apps import apps
        from django.db import connection
        from types import SimpleNamespace
        migration = importlib.import_module('visit.migrations.0088_asset_projects')
        migration.assign_existing_assets(apps, SimpleNamespace(connection=connection))

    def test_single_inactive_project_can_own_legacy_rows(self):
        project = Project.objects.create(name='Legacy', is_active=False)
        building = Building.objects.create(code='LEGACY-ONE')
        product = Product.objects.create(serial_number='LEGACY-ONE')
        self.migrate_data()
        building.refresh_from_db(); product.refresh_from_db()
        self.assertEqual(building.project_id, project.pk)
        self.assertEqual(product.project_id, project.pk)

    def test_conflicting_building_evidence_and_unlinked_rows_stay_unassigned(self):
        project = Project.objects.create(name='A')
        foreign = Project.objects.create(name='B')
        client = Client.objects.create(project=project)
        building = Building.objects.create(code='AMBIGUOUS')
        BuildingClient.objects.create(client=client, building=building)
        Visit.objects.create(building=building, type=VisitType.objects.create(project=foreign),
                             creator=User.objects.create(username='legacy-conflict'))
        unlinked = Building.objects.create(code='UNLINKED')
        self.migrate_data()
        building.refresh_from_db(); unlinked.refresh_from_db()
        self.assertIsNone(building.project_id)
        self.assertIsNone(unlinked.project_id)

    def test_unique_relations_propagate_project_to_parts(self):
        project = Project.objects.create(name='A')
        Project.objects.create(name='B')
        user = User.objects.create(username='legacy-migration')
        role = Role.objects.create(title='Legacy')
        RoleAssignment.objects.create(user=user, role=role, project=project)
        client = Client.objects.create()
        UserClient.objects.create(client=client, user=user)
        building = Building.objects.create(code='LEGACY-CHAIN')
        BuildingClient.objects.create(client=client, building=building)
        elevator = Elevator.objects.create()
        BuildingElevator.objects.create(building=building, elevator=elevator)
        model = ProductModel.objects.create()
        product = Product.objects.create(model=model)
        ProductElevator.objects.create(product=product, elevator=elevator)
        self.migrate_data()
        for row in (client, building, elevator, model, product):
            row.refresh_from_db()
            self.assertEqual(row.project_id, project.pk)
