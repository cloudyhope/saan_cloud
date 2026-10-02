from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import (
    AuthenticationValidationLog, Project, Role, RoleAssignment, RoleView, ViewMethod,
)
from survey.models import Survey, SurveyFillOut


class ValidationLogScopeTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Identity one')
        self.other_project = Project.objects.create(name='Identity two')
        self.user = User.objects.create(username='identity-manager')
        role = Role.objects.create(title='Identity manager', title_abbreviation='I', asset_scope='project')
        RoleAssignment.objects.create(user=self.user, project=self.project, role=role)
        for name, method in (
            ('UserDataValidationAPI', 'GET'), ('UserDataValidationAPI', 'POST'),
            ('AuthenticationValidationLogIsMainEditView', 'PATCH'),
        ):
            view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
            RoleView.objects.create(role=role, view_method_name=view_method,
                                    can_view=method == 'GET', can_create=method == 'POST',
                                    can_update=method == 'PATCH')
        own_fillout = SurveyFillOut.objects.create(survey=Survey.objects.create(
            project=self.project, name='Own survey'))
        self.other_fillout = SurveyFillOut.objects.create(survey=Survey.objects.create(
            project=self.other_project, name='Other survey'))
        self.own = AuthenticationValidationLog.objects.create(
            survey_fillout=own_fillout, national_id='1111111111', is_main=True)
        self.own_alternate = AuthenticationValidationLog.objects.create(
            survey_fillout=own_fillout, national_id='1111111112', is_main=False)
        self.foreign = AuthenticationValidationLog.objects.create(
            survey_fillout=self.other_fillout, national_id='2222222222', is_main=True)
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.list_url = f'/api/micro/personalinfo/validate/?p={self.project.pk}'

    def test_read_and_main_edit_remain_in_project(self):
        response = self.api.get(self.list_url)
        self.assertEqual(response.status_code, 200, response.data)
        rows = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual({row['id'] for row in rows}, {self.own.pk, self.own_alternate.pk})
        foreign_url = f'/api/micro/personalinfo/set_main/{self.foreign.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.patch(foreign_url, {'is_main': False}, format='json').status_code, 404)
        self.foreign.refresh_from_db()
        self.assertTrue(self.foreign.is_main)
        own_url = f'/api/micro/personalinfo/set_main/{self.own_alternate.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.patch(own_url, {'is_main': True}, format='json').status_code, 200)
        self.own.refresh_from_db()
        self.own_alternate.refresh_from_db()
        self.foreign.refresh_from_db()
        self.assertFalse(self.own.is_main)
        self.assertTrue(self.own_alternate.is_main)
        self.assertTrue(self.foreign.is_main)

    def test_cross_project_create_rejected_before_external_lookup(self):
        payload = {'survey_fillout': self.other_fillout.pk, 'national_id': '2222222222',
                   'phone_number': '09100000000', 'sheba_number': 'IR000000000000000000000000',
                   'birth_date': '2000-01-01'}
        with patch('auth_app.modules.uidshahkar.UIDShahkar') as external:
            response = self.api.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, 403)
        external.assert_not_called()
        self.assertEqual(AuthenticationValidationLog.objects.count(), 3)

    def test_unauthorized_user_cannot_list_identity_data(self):
        no_grant = User.objects.create(username='identity-no-grant')
        client = APIClient()
        client.force_authenticate(no_grant)
        self.assertEqual(client.get(self.list_url).status_code, 403)
        self.assertEqual(client.patch(
            f'/api/micro/personalinfo/set_main/{self.own.pk}/?p={self.project.pk}',
            {'is_main': False}, format='json').status_code, 403)
