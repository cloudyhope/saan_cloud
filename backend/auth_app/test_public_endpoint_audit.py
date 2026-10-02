from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIClient


class PublicEndpointAuditTests(TestCase):
    def test_district_edit_requires_active_project_grant(self):
        url = '/core/api/district/edits/1/?p=1'
        anonymous = APIClient()
        for method in ('get', 'patch', 'delete'):
            response = getattr(anonymous, method)(url)
            self.assertIn(response.status_code, (401, 403))

        user = get_user_model().objects.create_user(username='district-no-grant', password='test')
        client = APIClient()
        client.force_authenticate(user=user)
        self.assertEqual(client.patch(url, {'no': 2}, format='json').status_code, 403)

    def test_unrelated_short_url_service_is_unrouted(self):
        for path in (
            '/micro/shorturl/create/',
            '/s/example/',
            '/url_utility/api/v1/plan/list_create/',
            '/url_utility/api/v1/click_log/list_create/',
        ):
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)

    def test_unsafe_legacy_mutations_are_unrouted(self):
        for path in (
            '/core/api/core/register/',
            '/core/api/admin/fix_alarms/',
            '/config/generate_custom_qrcode/',
            '/api/config/v1/fr/result/',
            '/api/micro/config/value/1',
            '/core/api/auth/users/info/',
            '/core/api/auth/edit_profile/1/',
            '/api/auth/v1/company/list_create/',
            '/api/auth/v1/company/edits/1/',
            '/core/api/auth/document/edits/1/',
            '/core/api/auth/user_status/1/',
        ):
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)
