"""Security regressions run only against Django's isolated test database."""
from django.contrib.auth.models import User
from datetime import timedelta
from django.test import TestCase
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import (
    Project, Role, RoleAssignment, RoleView, ViewMethod, Limiter, RoleViewLimiter,
)
from auth_app.permissions import DeleteCreateUpdateGetPermission
from auth_app.serializers import UserOnlySerializer
from auth_app.user_serializers import SafeUserSerializer
from auth_app.views import (
    AuthUserOnlySerializer, UserSerializer, UserManagementSerializer,
    UsernamePasswordAPISerializer, ProjectSerializer,
)
from core.generics import BaseLimiter
from notification.views import UserSerializer as NotificationUserSerializer
from main.serializers import UserManagementSerializer as LegacyUserManagementSerializer
from visit.models import Building, Client, UserClient


class DefaultProtectedView(APIView):
    def get(self, request):
        return Response({'ok': True})


class LimitedUsersView(BaseLimiter, generics.ListAPIView):
    serializer_class = SafeUserSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.limit_queryset(User.objects.all())


class SecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='security-test', password='test-only-password')
        self.project = Project.objects.create(name='security-project')
        self.other_project = Project.objects.create(name='other-project')
        self.role = Role.objects.create(title='NoGrants', title_abbreviation='M', asset_scope='project')
        self.second_role = Role.objects.create(title='SecondRole', title_abbreviation='P', asset_scope='project')
        self.assignment = RoleAssignment.objects.create(
            user=self.user, role=self.role, project=self.project,
        )
        self.api = APIClient()
        self.building = Building.objects.create(code='SECURITY-BUILDING', verbose_name='Test', project=self.project)

    def grant(self, view, method='GET', role=None, **flags):
        vm, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
        defaults = {
            'can_view': method == 'GET', 'can_create': method == 'POST',
            'can_update': method in ('PATCH', 'PUT'), 'can_delete': method == 'DELETE',
        }
        defaults.update(flags)
        grant, _ = RoleView.objects.update_or_create(
            role=role or self.role, view_method_name=vm, defaults=defaults,
        )
        return grant

    def url(self, path):
        return f'{path}?p={self.project.pk}'

    def test_user_output_whitelist(self):
        private = {'password', 'groups', 'user_permissions', 'is_superuser', 'is_staff'}
        for serializer in (
            SafeUserSerializer, AuthUserOnlySerializer, UserSerializer,
            UserOnlySerializer, NotificationUserSerializer,
            UserManagementSerializer, UsernamePasswordAPISerializer,
            LegacyUserManagementSerializer,
        ):
            with self.subTest(serializer=serializer.__name__):
                data = serializer(self.user).data
                self.assertFalse(private.intersection(data))
                self.assertEqual(data['username'], self.user.username)

    def test_project_internal_key_is_not_in_nested_api_output(self):
        self.project.key = 'private-project-key'
        data = ProjectSerializer(self.project).data
        self.assertNotIn('key', data)
        self.assertEqual(data['id'], self.project.pk)

    def test_user_readonly_internal_fields(self):
        serializer = AuthUserOnlySerializer(self.user, data={
            'is_active': False, 'is_superuser': True, 'is_staff': True,
            'password': 'attempt-to-overwrite', 'first_name': 'Updated',
        }, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.check_password('test-only-password'))
        self.assertEqual(self.user.first_name, 'Updated')

    def test_password_inputs_remain_accepted(self):
        for cls in (UsernamePasswordAPISerializer, UserManagementSerializer, LegacyUserManagementSerializer):
            serializer = cls(data={'username': 'new-local-user', 'password': 'test-only-input'})
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertEqual(serializer.validated_data['password'], 'test-only-input')
            self.assertNotIn('password', serializer.data)

    def test_default_permission_requires_authentication(self):
        response = DefaultProtectedView.as_view()(APIRequestFactory().get('/'))
        self.assertIn(response.status_code, (401, 403))

    def test_all_entity_crud_methods_reject_anonymous_users(self):
        entities = (
            'Client', 'UserClient', 'ProductModel', 'Product', 'Elevator',
            'ProductElevator', 'Building', 'BuildingElevator', 'BuildingClient',
        )
        for entity in entities:
            for method, path in (
                ('get', f'/api/visit/{entity}ListCreate/'),
                ('post', f'/api/visit/{entity}ListCreate/'),
                ('get', f'/api/visit/{entity}Edits/999999/'),
                ('put', f'/api/visit/{entity}Edits/999999/'),
                ('patch', f'/api/visit/{entity}Edits/999999/'),
                ('delete', f'/api/visit/{entity}Edits/999999/'),
            ):
                with self.subTest(entity=entity, method=method):
                    response = getattr(self.api, method)(self.url(path))
                    self.assertIn(response.status_code, (401, 403))

    def test_authenticated_user_without_grant_is_denied(self):
        self.api.force_authenticate(self.user)
        response = self.api.get(self.url('/api/visit/BuildingListCreate/'))
        self.assertEqual(response.status_code, 403)

    def test_second_assigned_role_can_grant_access(self):
        RoleAssignment.objects.create(user=self.user, role=self.second_role, project=self.project)
        self.grant('BuildingListCreateAPIView', role=self.second_role)
        self.api.force_authenticate(self.user)
        response = self.api.get(self.url('/api/visit/BuildingListCreate/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.building.pk)

    def test_project_query_is_required_and_valid(self):
        self.grant('BuildingListCreateAPIView')
        self.api.force_authenticate(self.user)
        for query in ('', '?p=garbage', '?p=0', '?p=-1', f'?p={self.other_project.pk}'):
            with self.subTest(query=query):
                response = self.api.get('/api/visit/BuildingListCreate/' + query)
                self.assertEqual(response.status_code, 403)

    def test_deleted_assignment_is_denied(self):
        self.grant('BuildingListCreateAPIView')
        self.assignment.delete()
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get(self.url('/api/visit/BuildingListCreate/')).status_code, 403)

    def test_inactive_role_is_denied(self):
        self.grant('BuildingListCreateAPIView')
        self.role.is_active = False
        self.role.save()
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get(self.url('/api/visit/BuildingListCreate/')).status_code, 403)

    def test_inactive_project_is_denied(self):
        self.grant('BuildingListCreateAPIView')
        self.project.is_active = False
        self.project.save()
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get(self.url('/api/visit/BuildingListCreate/')).status_code, 403)

    def test_inactive_user_is_denied(self):
        self.grant('BuildingListCreateAPIView')
        self.user.is_active = False
        self.user.save()
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get(self.url('/api/visit/BuildingListCreate/')).status_code, 403)

    def test_read_grant_does_not_allow_writes(self):
        self.grant('BuildingListCreateAPIView')
        self.grant('BuildingEditsAPIView')
        self.api.force_authenticate(self.user)
        responses = [
            self.api.post(self.url('/api/visit/BuildingListCreate/'), {'code': 'ILLEGAL'}),
            self.api.patch(self.url(f'/api/visit/BuildingEdits/{self.building.pk}/'), {'code': 'ILLEGAL'}),
            self.api.put(self.url(f'/api/visit/BuildingEdits/{self.building.pk}/'), {'code': 'ILLEGAL'}),
            self.api.delete(self.url(f'/api/visit/BuildingEdits/{self.building.pk}/')),
        ]
        self.assertTrue(all(response.status_code == 403 for response in responses))
        self.building.refresh_from_db()
        self.assertEqual(self.building.code, 'SECURITY-BUILDING')
        self.assertFalse(Building.objects.filter(code='ILLEGAL').exists())

    def test_granted_patch_updates_building(self):
        self.grant('BuildingEditsAPIView', 'PATCH')
        self.api.force_authenticate(self.user)
        response = self.api.patch(self.url(f'/api/visit/BuildingEdits/{self.building.pk}/'), {'verbose_name': 'Updated'})
        self.assertEqual(response.status_code, 200)
        self.building.refresh_from_db()
        self.assertEqual(self.building.verbose_name, 'Updated')

    def test_head_and_options_use_read_grant(self):
        self.grant('BuildingListCreateAPIView')
        self.api.force_authenticate(self.user)
        for method in ('head', 'options'):
            self.assertEqual(getattr(self.api, method)(self.url('/api/visit/BuildingListCreate/')).status_code, 200)

    def test_nested_user_client_output_has_no_credentials(self):
        self.grant('UserClientListCreateAPIView')
        client = Client.objects.create(name='Security client', project=self.project)
        UserClient.objects.create(user=self.user, client=client)
        self.api.force_authenticate(self.user)
        response = self.api.get(self.url('/api/visit/UserClientListCreate/'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('password', response.data[0]['user'])
        self.assertNotIn('is_superuser', response.data[0]['user'])

    def test_health_and_password_login_remain_public(self):
        self.assertEqual(self.api.get('/health/').status_code, 200)
        response = self.api.post('/api/v1/username/password/token/', {
            'username': self.user.username, 'password': 'test-only-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        refreshed = self.api.post('/api/v1/username/password/refresh/', {'refresh': response.data['refresh']})
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn('refresh', refreshed.data)
        self.assertNotEqual(refreshed.data['refresh'], response.data['refresh'])
        self.assertEqual(self.api.post('/api/v1/username/password/refresh/',
                                       {'refresh': response.data['refresh']}).status_code, 401)
        self.assertEqual(self.api.post('/api/v1/username/password/logout/',
                                       {'refresh': refreshed.data['refresh']}).status_code, 200)
        self.assertEqual(self.api.post('/api/v1/username/password/refresh/',
                                       {'refresh': refreshed.data['refresh']}).status_code, 401)

    def test_expired_access_returns_401_for_client_refresh(self):
        expired = RefreshToken.for_user(self.user).access_token
        expired.set_exp(lifetime=timedelta(seconds=-1))
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(expired))
        response = client.get('/core/api/auth/me/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response['WWW-Authenticate'], 'Bearer realm="api"')

    def test_otp_verify_is_public_but_invalid_attempt_is_rejected(self):
        response = self.api.post('/core/api/auth/otp/verify/', {
            'id': 999999, 'code': 'invalid', 'verification_token': 'invalid',
            'phone_number': '09000000000',
        })
        self.assertEqual(response.status_code, 400)

    def limited_queryset(self, method='GET'):
        raw = getattr(APIRequestFactory(), method.lower())(self.url('/limited/'))
        force_authenticate(raw, self.user)
        view = LimitedUsersView()
        view.request = view.initialize_request(raw)
        # Materialize authentication before invoking the limiter directly.
        self.assertEqual(view.request.user, self.user)
        return view.get_queryset()

    def limiter(self, grant, key, value):
        row = Limiter.objects.create(key=key, value=value)
        return RoleViewLimiter.objects.create(role_view=grant, limiter=row, is_active=True)

    def test_limiter_ignores_other_role_configuration(self):
        self.grant('LimitedUsersView')
        foreign = self.grant('LimitedUsersView', role=self.second_role)
        self.limiter(foreign, 'id', '-1')
        self.assertEqual(set(self.limited_queryset().values_list('id', flat=True)), {self.user.pk})

    def test_limiter_conditions_within_role_use_and(self):
        grant = self.grant('LimitedUsersView')
        self.limiter(grant, 'id', str(self.user.pk))
        self.limiter(grant, 'username', 'different-user')
        self.assertFalse(self.limited_queryset().exists())

    def test_limiter_unions_scopes_of_authorized_roles(self):
        other = User.objects.create(username='another-local-user')
        RoleAssignment.objects.create(user=self.user, role=self.second_role, project=self.project)
        first = self.grant('LimitedUsersView')
        second = self.grant('LimitedUsersView', role=self.second_role)
        self.limiter(first, 'id', str(self.user.pk))
        self.limiter(second, 'id', str(other.pk))
        self.assertEqual(set(self.limited_queryset().values_list('id', flat=True)), {self.user.pk, other.pk})

    def test_limiter_applies_to_write_methods(self):
        other = User.objects.create(username='another-local-user')
        for method in ('PUT', 'PATCH', 'DELETE', 'POST'):
            with self.subTest(method=method):
                grant = self.grant('LimitedUsersView', method)
                self.limiter(grant, 'id', str(self.user.pk))
                result = self.limited_queryset(method)
                self.assertTrue(result.filter(pk=self.user.pk).exists())
                self.assertFalse(result.filter(pk=other.pk).exists())

    def test_limiter_user_placeholder(self):
        grant = self.grant('LimitedUsersView')
        self.limiter(grant, 'auth_app_roleassignment__user', '>M<')
        self.assertEqual(list(self.limited_queryset().values_list('id', flat=True)), [self.user.pk])

    def test_invalid_limiter_fails_closed(self):
        grant = self.grant('LimitedUsersView')
        self.limiter(grant, 'missing_field', 'anything')
        with self.assertLogs('core.generics', level='ERROR'):
            self.assertFalse(self.limited_queryset().exists())

    def test_limiter_without_authorized_grant_fails_closed(self):
        foreign = self.grant('LimitedUsersView', role=self.second_role)
        self.limiter(foreign, 'id', str(self.user.pk))
        self.assertFalse(self.limited_queryset().exists())
