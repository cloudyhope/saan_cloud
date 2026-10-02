from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Document, DocumentPhoto, Project, Role, RoleAssignment, RoleView, ViewMethod


class DocumentMediaAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Docs one')
        self.foreign_project = Project.objects.create(name='Docs two')
        self.user = User.objects.create(username='docs-owner')
        self.foreign = User.objects.create(username='docs-foreign')
        self.manager = User.objects.create(username='docs-manager')
        client_role = Role.objects.create(title='Docs client', title_abbreviation='C', asset_scope='client')
        manager_role = Role.objects.create(title='Docs manager', title_abbreviation='M', asset_scope='project')
        RoleAssignment.objects.create(user=self.user, role=client_role, project=self.project)
        RoleAssignment.objects.create(user=self.foreign, role=client_role, project=self.foreign_project)
        RoleAssignment.objects.create(user=self.manager, role=manager_role, project=self.project)
        for role, view, methods in (
            (client_role, 'DocumentsPhotoListCreateView', ('GET', 'POST')),
            (client_role, 'DocumentPhotoEditAPIView', ('GET',)),
            (manager_role, 'DocumentsPhotoListCreateView', ('GET',)),
            (manager_role, 'DocumentPhotoEditAPIView', ('GET', 'PATCH', 'DELETE')),
        ):
            for method in methods:
                view_method, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
                RoleView.objects.create(role=role, view_method_name=view_method,
                                        can_view=method == 'GET', can_create=method == 'POST',
                                        can_update=method == 'PATCH', can_delete=method == 'DELETE')
        self.document = Document.objects.create(name='Identity')
        self.other_photo = DocumentPhoto.objects.create(
            user=self.foreign, document=self.document,
            file='http://localhost:18110/media/uploads/foreign.pdf')
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def list_url(self):
        return f'/core/api/auth/document_photo/list_create/?p={self.project.pk}'

    def edit_url(self, photo):
        return f'/core/api/auth/document_photo_edits/{photo.pk}/?p={self.project.pk}'

    def test_upload_uses_owner_and_private_read_url(self):
        with patch('auth_app.views.ArvanStorage') as storage:
            storage.return_value.put_file.return_value = 'http://localhost:18110/media/uploads/own.pdf'
            invalid = self.api.post(self.list_url(), {
                'document': self.document.pk, 'file': SimpleUploadedFile('bad.pdf', b'not-pdf'),
            })
            self.assertEqual(invalid.status_code, 400)
            self.assertEqual(self.api.post(self.list_url(), {
                'document': self.document.pk, 'file': SimpleUploadedFile('good.pdf', b'%PDF-sample'),
                'user': self.foreign.pk,
            }).status_code, 400)
            self.assertEqual(storage.return_value.put_file.call_count, 0)
            response = self.api.post(self.list_url(), {
                'document': self.document.pk, 'file': SimpleUploadedFile('good.pdf', b'%PDF-sample'),
            })
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(DocumentPhoto.objects.get(pk=response.data['id']).user_id, self.user.pk)
            self.assertIn('/core/api/media/', response.data['file'])
            self.assertEqual(storage.return_value.put_file.call_count, 1)
            rows = self.api.get(self.list_url()).data
            self.assertEqual(len(rows), 1)
            self.assertEqual(self.api.get(self.edit_url(self.other_photo)).status_code, 404)

    def test_manager_scope_and_review_fields(self):
        own = DocumentPhoto.objects.create(
            user=self.user, document=self.document,
            file='http://localhost:18110/media/uploads/own.pdf')
        self.assertEqual(self.api.patch(self.edit_url(own), {'is_checked': True}, format='json').status_code, 403)
        self.api.force_authenticate(self.manager)
        rows = self.api.get(self.list_url()).data
        self.assertEqual([row['id'] for row in rows], [own.pk])
        self.assertEqual(self.api.get(self.edit_url(self.other_photo)).status_code, 404)
        self.assertEqual(self.api.patch(self.edit_url(own), {'file': 'http://localhost:18110/media/uploads/other.pdf'}, format='json').status_code, 400)
        self.assertEqual(self.api.patch(self.edit_url(own), {'is_checked': True}, format='json').status_code, 200)
        own.refresh_from_db()
        self.assertTrue(own.is_checked)
