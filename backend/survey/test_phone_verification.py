"""Survey phone challenge is scoped, short-lived and single-use."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from survey.models import FillOutPhoneVerification, Survey, SurveyFillOut


class SurveyPhoneVerificationTests(TestCase):
    phone = '09123456789'

    def setUp(self):
        self.project = Project.objects.create(name='Phone project')
        self.other_project = Project.objects.create(name='Other phone project')
        self.user = User.objects.create(username='survey-phone-user')
        role = Role.objects.create(title='Survey phone role', title_abbreviation='S',
                                   asset_scope='project')
        RoleAssignment.objects.create(user=self.user, project=self.project, role=role)
        for name in ('FillOutPhoneVerificationRequestView', 'FillOutPhoneVerificationCheckCodeView'):
            method, _ = ViewMethod.objects.get_or_create(view_name=name, method='POST')
            RoleView.objects.create(role=role, view_method_name=method, can_create=True)
        survey = Survey.objects.create(project=self.project, has_phone_verification=True)
        other = Survey.objects.create(project=self.other_project, has_phone_verification=True)
        self.fillout = SurveyFillOut.objects.create(survey=survey, user=self.user)
        self.foreign = SurveyFillOut.objects.create(survey=other)
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.request_url = f'/core/api/promoter/verification_code/request/?p={self.project.pk}'
        self.verify_url = f'/core/api/promoter/verification_code/validate/?p={self.project.pk}'

    def issue(self):
        with patch('notification.modules.notification.Notification') as sms:
            response = self.api.post(self.request_url, {
                'survey_fill_out': self.fillout.pk, 'phone_number': self.phone,
            }, format='json', REMOTE_ADDR='192.0.2.22')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data, sms.call_args.kwargs['code']

    def verify(self, data, code):
        return self.api.post(self.verify_url, {
            'id': data['id'], 'verification_token': data['verification_token'],
            'phone_number': self.phone, 'code': code,
        }, format='json', REMOTE_ADDR='192.0.2.23')

    def test_single_use_and_hidden_code(self):
        issued, code = self.issue()
        challenge = FillOutPhoneVerification.objects.get(pk=issued['id'])
        self.assertNotIn(code, str(issued))
        self.assertNotEqual(challenge.code, code)
        self.assertTrue(challenge.code.startswith('pbkdf2_'))
        self.assertEqual(self.verify(issued, code).status_code, 200)
        self.assertEqual(self.verify(issued, code).status_code, 400)
        challenge.refresh_from_db()
        self.assertIsNotNone(challenge.consumed_at)
        self.assertEqual(challenge.code, '')
        self.fillout.refresh_from_db()
        self.assertTrue(self.fillout.phone_verified)

    def test_scope_expiry_attempts_and_resend(self):
        response = self.api.post(self.request_url, {'survey_fill_out': self.foreign.pk,
                                                    'phone_number': self.phone}, format='json')
        self.assertEqual(response.status_code, 404)
        issued, code = self.issue()
        self.assertEqual(self.api.post(self.request_url, {'survey_fill_out': self.fillout.pk,
                                                         'phone_number': self.phone}, format='json').status_code, 429)
        wrong = '00000' if code != '00000' else '11111'
        for _ in range(3):
            self.assertEqual(self.verify(issued, wrong).status_code, 400)
        self.assertEqual(self.verify(issued, code).status_code, 400)
        FillOutPhoneVerification.objects.filter(pk=issued['id']).update(
            datetime_requested=timezone.now() - timedelta(minutes=3))
        second, valid_code = self.issue()
        FillOutPhoneVerification.objects.filter(pk=second['id']).update(
            datetime_requested=timezone.now() - timedelta(minutes=3))
        self.assertEqual(self.verify(second, valid_code).status_code, 419)
