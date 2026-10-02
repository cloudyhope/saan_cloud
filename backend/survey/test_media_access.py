"""Survey media must remain inside its project and accepted fill-out."""
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from survey.models import Survey, SurveyFillOut, SurveyPhoto, SurveyPhotoType


class SurveyMediaAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Survey media one')
        self.other_project = Project.objects.create(name='Survey media two')
        self.manager = User.objects.create(username='survey-manager')
        self.other_user = User.objects.create(username='survey-other')
        role = Role.objects.create(title='Survey media manager', title_abbreviation='S',
                                   asset_scope='project')
        RoleAssignment.objects.create(user=self.manager, project=self.project, role=role)
        for view_name, method in (
            ('SurveyPhotoListCreateView', 'GET'),
            ('SurveyPhotoEditsView', 'GET'), ('SurveyPhotoEditsView', 'PATCH'),
            ('SurveyPhotoEditsView', 'DELETE'), ('SurveyPhotoTypeEditsView', 'GET'),
            ('SurveyPhotoTypeEditsView', 'PATCH'), ('SurveyPhotoTypeListCreateView', 'POST'),
            ('PromoterUploadSurveyImageAPIView', 'POST'),
            ('SurveyChangePhotoLocations', 'POST'),
        ):
            view_method, _ = ViewMethod.objects.get_or_create(view_name=view_name, method=method)
            RoleView.objects.create(role=role, view_method_name=view_method,
                                    can_view=method == 'GET', can_create=method == 'POST',
                                    can_update=method == 'PATCH', can_delete=method == 'DELETE')
        self.survey = Survey.objects.create(project=self.project, name='Survey one')
        self.other_survey = Survey.objects.create(project=self.other_project, name='Survey two')
        self.fillout = SurveyFillOut.objects.create(survey=self.survey, user=self.manager)
        self.other_fillout = SurveyFillOut.objects.create(survey=self.other_survey, user=self.other_user)
        self.photo_type = SurveyPhotoType.objects.create(survey=self.survey, name='Door', max=1)
        self.other_type = SurveyPhotoType.objects.create(survey=self.other_survey, name='Window')
        self.photo = SurveyPhoto.objects.create(survey_photo_type=self.photo_type,
                                                survey_fill_out=self.fillout, creator=self.manager,
                                                link='https://example.test/door.png')
        self.other_photo = SurveyPhoto.objects.create(survey_photo_type=self.other_type,
                                                      survey_fill_out=self.other_fillout,
                                                      creator=self.other_user,
                                                      link='https://example.test/window.png')
        self.api = APIClient()
        self.api.force_authenticate(self.manager)

    def photo_url(self, photo):
        return f'/core/api/admin/survey_photo/edits/{photo.pk}/?p={self.project.pk}'

    def upload(self, *, photo_type=None, fillout=None, file=None):
        return self.api.post(
            f'/core/api/promoter/upload_survey_photo/?p={self.project.pk}',
            {'survey_photo_type': (photo_type or self.photo_type).pk,
             'survey_fill_out': (fillout or self.fillout).pk,
             'link': file or self.image(), 'longitude': 'null'}, format='multipart',
        )

    @staticmethod
    def image():
        buffer = BytesIO()
        Image.new('RGB', (2, 2), 'white').save(buffer, format='PNG')
        return SimpleUploadedFile('door.png', buffer.getvalue(), content_type='image/png')

    def test_list_edits_and_photo_type_are_project_scoped(self):
        response = self.api.get(f'/core/api/admin/survey_photo/list_create/?p={self.project.pk}')
        self.assertEqual(response.status_code, 200, response.data)
        rows = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual([row['id'] for row in rows], [self.photo.pk])
        self.assertEqual(self.api.get(self.photo_url(self.other_photo)).status_code, 404)
        self.assertEqual(self.api.patch(self.photo_url(self.other_photo),
                                        {'is_checked': True}, format='json').status_code, 404)
        self.assertEqual(self.api.delete(self.photo_url(self.other_photo)).status_code, 404)
        self.assertEqual(self.api.get(
            f'/core/api/admin/survey_photo_type/edits/{self.other_type.pk}/?p={self.project.pk}'
        ).status_code, 404)
        self.assertEqual(self.api.patch(
            f'/core/api/admin/survey_photo_type/edits/{self.photo_type.pk}/?p={self.project.pk}',
            {'survey': self.other_survey.pk}, format='json').status_code, 400)
        self.assertEqual(self.api.post(
            f'/core/api/admin/survey_photo_type/list_create/?p={self.project.pk}',
            {'survey': self.other_survey.pk, 'name': 'Foreign'}, format='json').status_code, 400)
        self.assertEqual(self.api.patch(self.photo_url(self.photo),
                                        {'link': 'https://example.test/new.png'}, format='json').status_code, 400)
        self.photo.refresh_from_db()
        self.assertTrue(self.photo.link.endswith('door.png'))
        self.assertEqual(self.api.delete(self.photo_url(self.photo)).status_code, 204)
        self.photo.refresh_from_db()
        self.assertTrue(self.photo.is_deleted)

    @patch('survey.views.ArvanStorage')
    def test_upload_checks_project_type_file_state_and_limit_before_storage(self, storage):
        self.assertEqual(self.upload(fillout=self.other_fillout).status_code, 403)
        self.assertEqual(self.upload(photo_type=self.other_type).status_code, 400)
        bad_file = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        self.assertEqual(self.upload(file=bad_file).status_code, 400)
        self.fillout.is_closed = True
        self.fillout.save()
        self.assertEqual(self.upload().status_code, 400)
        self.fillout.is_closed = False
        self.fillout.save()
        self.assertEqual(self.upload().status_code, 400)  # max=1, existing photo
        storage.assert_not_called()

        self.photo.delete()
        storage.return_value.put_file.return_value = 'https://example.test/new.png'
        response = self.upload()
        self.assertEqual(response.status_code, 201, response.data)
        storage.return_value.put_file.assert_called_once()
        uploaded = SurveyPhoto.objects.get(pk=response.data['id'])
        self.assertEqual(uploaded.survey_fill_out_id, self.fillout.pk)
        self.assertEqual(uploaded.creator_id, self.manager.pk)
        self.assertIsNone(uploaded.longitude)
        self.assertEqual(self.upload().status_code, 400)
        self.assertEqual(storage.return_value.put_file.call_count, 1)

    def test_location_batch_rejects_foreign_photo_atomically(self):
        url = f'/core/api/admin/survey/change_photo_location/?p={self.project.pk}'
        response = self.api.post(url, {'ids': [self.photo.pk, self.other_photo.pk],
                                       'latitude': '35.0000000000000000',
                                       'longitude': '51.0000000000000000'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.photo.refresh_from_db()
        self.assertIsNone(self.photo.latitude)
        response = self.api.post(url, {'ids': [self.photo.pk],
                                       'latitude': '35.0000000000000000',
                                       'longitude': '51.0000000000000000'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.photo.refresh_from_db()
        self.assertEqual(str(self.photo.latitude), '35.0000000000000000')
