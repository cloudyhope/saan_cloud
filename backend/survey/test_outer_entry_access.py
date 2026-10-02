from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from survey.models import OuterEntryConfig, Survey


class OuterEntryConfigAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Outer entry one')
        self.other_project = Project.objects.create(name='Outer entry two')
        self.user = User.objects.create(username='outer-manager')
        role = Role.objects.create(title='Outer manager', title_abbreviation='O', asset_scope='project')
        RoleAssignment.objects.create(user=self.user, project=self.project, role=role)
        for name, method in (
            ('OuterEntryConfigListCreateView', 'GET'),
            ('OuterEntryConfigListCreateView', 'POST'),
            ('OuterEntryConfigEditsView', 'GET'),
            ('OuterEntryConfigEditsView', 'PATCH'),
            ('OuterEntryConfigEditsView', 'DELETE'),
        ):
            view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
            RoleView.objects.create(role=role, view_method_name=view_method,
                                    can_view=method == 'GET', can_create=method == 'POST',
                                    can_update=method == 'PATCH', can_delete=method == 'DELETE')
        self.survey = Survey.objects.create(project=self.project, name='Own survey')
        self.other_survey = Survey.objects.create(project=self.other_project, name='Other survey')
        self.own = OuterEntryConfig.objects.create(project=self.project, survey=self.survey)
        self.foreign = OuterEntryConfig.objects.create(project=self.other_project, survey=self.other_survey)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.list_url = f'/config/outer_survey_config/list_create/?p={self.project.pk}'

    def test_project_scope_and_write_validation(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        rows = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual([row['id'] for row in rows], [self.own.pk])
        foreign_url = f'/config/outer_survey_config/edits/{self.foreign.pk}/?p={self.project.pk}'
        self.assertEqual(self.client.get(foreign_url).status_code, 404)
        self.assertEqual(self.client.patch(foreign_url, {'url': 'changed'}, format='json').status_code, 404)
        self.assertEqual(self.client.post(self.list_url, {'survey': self.other_survey.pk}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.list_url, {'project': self.other_project.pk,
                                                         'survey': self.survey.pk}, format='json').status_code, 400)
        response = self.client.post(self.list_url, {'survey': self.survey.pk}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(OuterEntryConfig.objects.get(pk=response.data['id']).project_id, self.project.pk)

    def test_public_and_ungranted_access_is_closed(self):
        anonymous = APIClient()
        self.assertIn(anonymous.get(self.list_url).status_code, (401, 403))
        self.assertIn(anonymous.post(self.list_url, {'survey': self.survey.pk}, format='json').status_code,
                      (401, 403))
        other = User.objects.create(username='outer-no-grant')
        client = APIClient()
        client.force_authenticate(other)
        self.assertEqual(client.get(self.list_url).status_code, 403)
        with self.assertRaises(Resolver404):
            resolve(f'/survey/outer_survey_qrcode/{self.own.pk}/')
