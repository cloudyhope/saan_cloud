"""OTP contract and abuse protection on the isolated test database."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import OTP


class OTPTests(TestCase):
    phone = '09123456789'

    def setUp(self):
        User.objects.create_user(username=self.phone, password='test-only-password')
        self.api = APIClient()
        self.remote_id = 1

    def post(self, path, payload):
        # Keep the cache-backed IP throttle independent between assertions.
        self.remote_id += 1
        return self.api.post(path, payload, REMOTE_ADDR=f'192.0.2.{self.remote_id}')

    def request_code(self):
        with patch('notification.modules.notification.Notification') as notification:
            response = self.post('/core/api/auth/otp/request/', {'phone_number': self.phone})
        self.assertEqual(response.status_code, 201, response.data)
        code = notification.call_args.kwargs['code']
        return response, code

    def verify(self, request_response, code):
        return self.post('/core/api/auth/otp/verify/', {
            'id': request_response.data['id'],
            'verification_token': request_response.data['verification_token'],
            'phone_number': self.phone,
            'code': code,
        })

    def test_code_is_secret_hashed_and_single_use(self):
        request_response, code = self.request_code()
        self.assertNotIn('otp', request_response.data)
        self.assertNotIn(code, str(request_response.data))
        otp = OTP.objects.get(pk=request_response.data['id'])
        self.assertNotEqual(otp.otp, code)
        self.assertTrue(otp.otp.startswith('pbkdf2_'))
        accepted = self.verify(request_response, code)
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertIn('access', accepted.data['tokens'])
        self.assertEqual(self.verify(request_response, code).status_code, 400)
        otp.refresh_from_db()
        self.assertIsNotNone(otp.consumed_at)
        self.assertEqual(otp.otp, '')
        self.assertEqual(otp.verification_token, '')

    def test_three_wrong_attempts_lock_the_challenge(self):
        request_response, code = self.request_code()
        wrong_code = '00000' if code != '00000' else '11111'
        for _ in range(3):
            self.assertEqual(self.verify(request_response, wrong_code).status_code, 400)
        self.assertEqual(self.verify(request_response, code).status_code, 400)
        self.assertEqual(OTP.objects.get(pk=request_response.data['id']).failed_attempts, 3)

    def test_expiry_and_resend_limits(self):
        first, code = self.request_code()
        self.assertEqual(self.post('/core/api/auth/otp/request/', {'phone_number': self.phone}).status_code, 429)
        OTP.objects.filter(pk=first.data['id']).update(datetime_requested=timezone.now() - timedelta(minutes=3))
        self.assertEqual(self.verify(first, code).status_code, 419)
        second, _ = self.request_code()
        self.assertIsNotNone(OTP.objects.get(pk=first.data['id']).consumed_at)
        OTP.objects.filter(pk=second.data['id']).update(datetime_requested=timezone.now() - timedelta(minutes=1))
        for _ in range(3):
            latest, _ = self.request_code()
            OTP.objects.filter(pk=latest.data['id']).update(datetime_requested=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.post('/core/api/auth/otp/request/', {'phone_number': self.phone}).status_code, 429)

    def test_untrusted_payload_cannot_write_code_or_bypass_phone_validation(self):
        with patch('notification.modules.notification.Notification'):
            response = self.post('/core/api/auth/otp/request/', {
                'phone_number': self.phone, 'otp': '12345', 'failed_attempts': 0,
            })
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(OTP.objects.get(pk=response.data['id']).otp, '12345')
        self.assertEqual(self.post('/core/api/auth/otp/request/', {'phone_number': 'bad'}).status_code, 400)
