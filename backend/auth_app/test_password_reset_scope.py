from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod


class PasswordResetScopeTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Password one')
        self.other_project = Project.objects.create(name='Password two')
        manager = Role.objects.create(title='Password manager', title_abbreviation='M',
                                      asset_scope='project', priority=1)
        worker = Role.objects.create(title='Password worker', title_abbreviation='W',
                                     asset_scope='assigned', priority=5)
        self.worker_alt = Role.objects.create(title='Password alternate', title_abbreviation='A',
                                              asset_scope='assigned', priority=6)
        self.actor = User.objects.create_user(username='password-actor', password='BeforeActor!2026')
        self.target = User.objects.create_user(username='password-target', password='BeforeTarget!2026')
        self.foreign = User.objects.create_user(username='password-foreign', password='BeforeForeign!2026')
        self.peer = User.objects.create_user(username='password-peer', password='BeforePeer!2026')
        RoleAssignment.objects.create(user=self.actor, project=self.project, role=manager)
        self.target_assignment = RoleAssignment.objects.create(user=self.target, project=self.project, role=worker)
        self.foreign_assignment = RoleAssignment.objects.create(user=self.foreign, project=self.other_project, role=worker)
        RoleAssignment.objects.create(user=self.peer, project=self.project, role=manager)
        method = ViewMethod.objects.create(view_name='SetPasswordForUser', method='POST')
        RoleView.objects.create(role=manager, view_method_name=method, can_create=True)
        role_method = ViewMethod.objects.create(view_name='UserManagementView', method='POST')
        RoleView.objects.create(role=manager, view_method_name=role_method, can_create=True)
        delete_method = ViewMethod.objects.create(view_name='RolesAssignmentDeleteListView', method='DELETE')
        RoleView.objects.create(role=manager, view_method_name=delete_method, can_delete=True)
        role_create_method = ViewMethod.objects.create(view_name='RoleListView', method='POST')
        RoleView.objects.create(role=manager, view_method_name=role_create_method, can_create=True)
        document_create_method = ViewMethod.objects.create(view_name='DocumentsListCreteView', method='POST')
        RoleView.objects.create(role=manager, view_method_name=document_create_method, can_create=True)
        for view_name in ('UserInquiryView', 'RolesAssignmentCustomizableListView'):
            method = ViewMethod.objects.create(view_name=view_name, method='GET')
            RoleView.objects.create(role=manager, view_method_name=method, can_view=True)
            RoleView.objects.create(role=worker, view_method_name=method, can_view=True)
        self.api = APIClient()
        self.api.force_authenticate(self.actor)
        self.url = f'/auth/api/v1/auth/set-password/?p={self.project.pk}'

    def test_manager_can_reset_only_lower_rank_account_in_same_project(self):
        response = self.api.post(self.url, {'username': self.target.username,
                                            'password': 'StrongExample!2026'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password('StrongExample!2026'))
        self.assertEqual(self.api.post(self.url, {'username': self.foreign.username,
                                                  'password': 'AnotherStrong!2026'}, format='json').status_code, 404)
        self.assertEqual(self.api.post(self.url, {'username': self.peer.username,
                                                  'password': 'AnotherStrong!2026'}, format='json').status_code, 403)
        self.foreign.refresh_from_db()
        self.peer.refresh_from_db()
        self.assertTrue(self.foreign.check_password('BeforeForeign!2026'))
        self.assertTrue(self.peer.check_password('BeforePeer!2026'))

    def test_short_password_and_ungranted_calls_fail(self):
        self.assertEqual(self.api.post(self.url, {'username': self.target.username,
                                                  'password': 'short'}, format='json').status_code, 400)
        no_grant = APIClient()
        no_grant.force_authenticate(User.objects.create_user(username='password-no-grant'))
        self.assertEqual(no_grant.post(self.url, {'username': self.target.username,
                                                  'password': 'StrongExample!2026'}, format='json').status_code, 403)
        anonymous = APIClient()
        self.assertIn(anonymous.post(self.url, {'username': self.target.username,
                                                 'password': 'StrongExample!2026'}, format='json').status_code,
                      (401, 403))
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password('BeforeTarget!2026'))
        with self.assertRaises(Resolver404):
            resolve('/auth/api/v1/auth/bulk-set-password/')

    def test_project_manager_cannot_reset_shared_account_password(self):
        worker = self.target_assignment.role
        RoleAssignment.objects.create(user=self.target, project=self.other_project, role=worker)
        response = self.api.post(self.url, {
            'username': self.target.username, 'password': 'SharedAccount!2026',
        }, format='json')
        self.assertEqual(response.status_code, 403)
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password('BeforeTarget!2026'))

    def test_role_change_uses_existing_membership_and_ignores_account_overpost(self):
        url = f'/api/auth/v1/user/management/?p={self.project.pk}'
        response = self.api.post(url, {
            'id': self.target_assignment.pk, 'project': self.project.pk,
            'role': self.worker_alt.pk,
            'user': {'username': self.target.username, 'password': 'ForgedPassword!2026'},
            'change_password': True,
        }, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.target_assignment.refresh_from_db()
        self.target.refresh_from_db()
        self.assertNotEqual(self.target_assignment.role_id, self.worker_alt.pk)
        self.assertTrue(self.target.check_password('BeforeTarget!2026'))
        response = self.api.post(url, {
            'id': self.target_assignment.pk, 'project': self.project.pk,
            'role': self.worker_alt.pk,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.target_assignment.refresh_from_db()
        self.assertEqual(self.target_assignment.role_id, self.worker_alt.pk)
        self.assertTrue(self.target.check_password('BeforeTarget!2026'))
        self.assertEqual(self.api.post(url, {
            'id': self.foreign_assignment.pk, 'project': self.project.pk,
            'role': self.worker_alt.pk,
        }, format='json').status_code, 404)
        self.assertEqual(self.api.post(url, {
            'id': self.target_assignment.pk, 'project': self.other_project.pk,
            'role': self.worker_alt.pk,
        }, format='json').status_code, 400)

    def test_role_change_cannot_demote_a_peer_through_second_membership(self):
        manager = Role.objects.get(title='Password manager')
        RoleAssignment.objects.create(user=self.target, project=self.project, role=manager)
        url = f'/api/auth/v1/user/management/?p={self.project.pk}'
        response = self.api.post(url, {
            'id': self.target_assignment.pk, 'project': self.project.pk,
            'role': self.worker_alt.pk,
        }, format='json')
        self.assertEqual(response.status_code, 403)
        self.target_assignment.refresh_from_db()
        self.assertNotEqual(self.target_assignment.role_id, self.worker_alt.pk)

    def test_membership_delete_is_project_and_rank_scoped(self):
        def url(assignment_id):
            return f'/core/api/admin/role_assignment/delete/{assignment_id}/?p={self.project.pk}'

        self.assertEqual(self.api.delete(url(self.foreign_assignment.pk)).status_code, 404)
        peer_assignment = RoleAssignment.objects.get(user=self.peer, project=self.project)
        self.assertEqual(self.api.delete(url(peer_assignment.pk)).status_code, 403)
        self.assertEqual(self.api.delete(url(self.target_assignment.pk)).status_code, 204)
        self.target_assignment.refresh_from_db()
        self.assertTrue(self.target_assignment.is_deleted)
        self.foreign_assignment.refresh_from_db()
        self.assertFalse(self.foreign_assignment.is_deleted)
        self.assertFalse(peer_assignment.is_deleted)

    def test_unscoped_login_toggle_route_is_removed(self):
        with self.assertRaises(Resolver404):
            resolve(f'/api/v1/user/can_login_toggle/{self.target.username}/')

    def test_role_catalog_cannot_create_global_role(self):
        response = self.api.post(
            f'/core/api/auth/roles/list_create/?p={self.project.pk}',
            {'title': 'Forged manager', 'title_abbreviation': 'F',
             'priority': 0, 'asset_scope': 'project'},
            format='json',
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Role.objects.filter(title='Forged manager').exists())

    def test_document_type_catalog_is_read_only(self):
        response = self.api.post(
            f'/core/api/auth/document/list_create/?p={self.project.pk}',
            {'name': 'Forged identity document', 'is_mandatory': True},
            format='json',
        )
        self.assertEqual(response.status_code, 405)

    def test_new_user_has_no_default_password_and_existing_account_is_not_attached(self):
        url = f'/api/auth/v1/user/management/?p={self.project.pk}'
        data = {
            'username': '09100000077', 'first_name': 'New', 'last_name': 'Worker',
            'project': self.project.pk, 'role': self.worker_alt.pk,
        }
        response = self.api.post(url, data, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        created = User.objects.get(username=data['username'])
        self.assertFalse(created.has_usable_password())
        self.assertTrue(RoleAssignment.objects.filter(
            user=created, project=self.project, role=self.worker_alt,
        ).exists())
        self.assertEqual(self.api.post(url, data, format='json').status_code, 400)
        existing = User.objects.create_user(username='09100000079', password='Existing!2026')
        RoleAssignment.objects.create(user=existing, project=self.other_project, role=self.worker_alt)
        foreign_data = {**data, 'username': existing.username}
        self.assertEqual(self.api.post(url, foreign_data, format='json').status_code, 400)
        self.assertFalse(RoleAssignment.objects.filter(
            user=existing, project=self.project,
        ).exists())

    def test_new_user_rejects_privileged_role_and_invalid_identity(self):
        url = f'/api/auth/v1/user/management/?p={self.project.pk}'
        data = {
            'username': '09100000078', 'first_name': 'New', 'last_name': 'Worker',
            'project': self.project.pk, 'role': self.worker_alt.pk,
            'national_code': '1111111111',
        }
        self.assertEqual(self.api.post(url, data, format='json').status_code, 400)
        manager = Role.objects.get(title='Password manager')
        self.assertEqual(self.api.post(url, {
            **data, 'national_code': '', 'role': manager.pk,
        }, format='json').status_code, 403)
        self.assertFalse(User.objects.filter(username=data['username']).exists())

    def test_user_roster_requires_project_wide_grant(self):
        paths = (
            '/api/auth/v1/user/inquiry/',
            '/core/api/admin/role_assignment/list/',
        )
        worker_api = APIClient()
        worker_api.force_authenticate(self.target)
        for path in paths:
            url = f'{path}?p={self.project.pk}'
            self.assertEqual(worker_api.get(url).status_code, 403)
            response = self.api.get(url)
            self.assertEqual(response.status_code, 200, response.data)
            rows = response.data if isinstance(response.data, list) else response.data['results']
            self.assertTrue(rows)
            self.assertTrue(all(row['project']['id'] == self.project.pk for row in rows))
