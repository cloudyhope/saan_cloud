"""Educational media are scoped to a project and exposed by temporary URLs."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, UploadedFile, ViewMethod


class UploadedFileAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Media project')
        self.foreign = Project.objects.create(name='Foreign media')
        self.user = User.objects.create(username='media-manager')
        self.other = User.objects.create(username='media-other')
        self.manager = Role.objects.create(title='Media manager', title_abbreviation='M',
                                           asset_scope='project')
        self.client = Role.objects.create(title='Media client', title_abbreviation='C',
                                          asset_scope='client')
        RoleAssignment.objects.create(user=self.user, role=self.manager, project=self.project)
        RoleAssignment.objects.create(user=self.other, role=self.client, project=self.project)
        for role in (self.manager, self.client):
            for view, methods in (('UploadedFileListCreateView', ('GET', 'POST')),
                                  ('UploadedFileEditView', ('GET', 'PATCH', 'DELETE'))):
                for method in methods:
                    vm, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
                    RoleView.objects.create(role=role, view_method_name=vm,
                        can_view=method == 'GET', can_create=method == 'POST',
                        can_update=method == 'PATCH', can_delete=method == 'DELETE')
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.url = f'/config/files/list_create/?p={self.project.pk}'

    def upload(self, **extra):
        data = {
            'file': SimpleUploadedFile('guide.pdf', b'%PDF-guide', content_type='application/pdf'),
            'icon': SimpleUploadedFile('icon.png', b'\x89PNG\r\n\x1a\nicon', content_type='image/png'),
            'project': self.project.pk, 'name': 'Guide', 'type': 'EDU',
        }
        data.update(extra)
        return self.api.post(self.url, data, format='multipart')

    def test_upload_validates_project_fields_and_private_read_links(self):
        self.api.force_authenticate(self.other)
        self.assertEqual(self.upload().status_code, 403)
        self.api.force_authenticate(self.user)
        with patch('auth_app.views.ArvanStorage') as storage:
            storage.return_value.put_file.side_effect = [
                'http://localhost:18110/media/uploads/guide.pdf',
                'http://localhost:18110/media/uploads/icon.png',
            ]
            self.assertEqual(self.upload(project=self.foreign.pk).status_code, 400)
            self.assertEqual(self.upload(uploaded_by=self.other.pk).status_code, 400)
            self.assertEqual(self.upload(file=SimpleUploadedFile('bad.pdf', b'bad')).status_code, 400)
            self.assertEqual(storage.return_value.put_file.call_count, 0)
            response = self.upload()
            self.assertEqual(response.status_code, 201, response.data)
            self.assertIn('/core/api/media/', response.data['file'])
            self.assertIn('/core/api/media/', response.data['icon'])
            record = UploadedFile.objects.get(pk=response.data['id'])
            self.assertEqual((record.project_id, record.uploaded_by_id),
                             (self.project.pk, self.user.pk))
            self.assertEqual(storage.return_value.put_file.call_count, 2)

    def test_list_edit_and_soft_delete_remain_in_project(self):
        own = UploadedFile.objects.create(project=self.project, uploaded_by=self.user,
            name='Own', type='EDU', file='http://localhost:18110/media/uploads/own.pdf')
        global_file = UploadedFile.objects.create(name='Global', type='EDU')
        foreign = UploadedFile.objects.create(project=self.foreign, name='Foreign', type='EDU')
        self.assertEqual([row['id'] for row in self.api.get(self.url).data], [own.pk])
        global_rows = self.api.get(self.url + '&project__isnull=true').data
        self.assertEqual({row['id'] for row in global_rows}, {global_file.pk})
        own_url = f'/core/api/config/files/edits/{own.pk}/?p={self.project.pk}'
        foreign_url = f'/core/api/config/files/edits/{foreign.pk}/?p={self.project.pk}'
        self.assertEqual(self.api.get(foreign_url).status_code, 404)
        self.assertEqual(self.api.patch(own_url, {'project': self.foreign.pk}, format='json').status_code, 400)
        self.assertEqual(self.api.patch(own_url, {'name': 'Updated'}, format='json').status_code, 200)
        own.refresh_from_db()
        self.assertEqual(own.name, 'Updated')
        self.assertEqual(self.api.delete(own_url).status_code, 204)
        own.refresh_from_db()
        self.assertTrue(own.is_deleted)
