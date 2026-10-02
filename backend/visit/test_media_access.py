"""Admin photo operations must never cross a project or rewrite file ownership."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import ExtendedUser, Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Building, Photo, PhotoType, Visit, VisitType


class AdminMediaAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Media one')
        self.foreign_project = Project.objects.create(name='Media two')
        self.manager = User.objects.create(username='media-manager')
        ExtendedUser.objects.create(user=self.manager, role=ExtendedUser.MANAGER)
        role = Role.objects.create(title='Media manager', title_abbreviation='M', asset_scope='project')
        RoleAssignment.objects.create(user=self.manager, project=self.project, role=role)
        for view_name, method in (
            ('AdminPhotoListView', 'GET'), ('AdminPhotoEditsView', 'GET'),
            ('AdminPhotoEditsView', 'PATCH'), ('AdminPhotoEditsView', 'DELETE'),
            ('PhotoTypeRetrieveView', 'GET'),
        ):
            view_method, _ = ViewMethod.objects.get_or_create(view_name=view_name, method=method)
            RoleView.objects.create(role=role, view_method_name=view_method,
                                    can_view=method == 'GET', can_update=method == 'PATCH',
                                    can_delete=method == 'DELETE')
        self.own = self.photo(self.project, 'ONE')
        self.foreign = self.photo(self.foreign_project, 'TWO')
        self.api = APIClient()
        self.api.force_authenticate(self.manager)

    def photo(self, project, suffix):
        building = Building.objects.create(project=project, code='B-' + suffix)
        visit_type = VisitType.objects.create(project=project, title='Repair')
        visit = Visit.objects.create(type=visit_type, building=building, creator=self.manager)
        photo_type = PhotoType.objects.create(project=project, visit_type=visit_type,
                                              name='Inspection')
        return Photo.objects.create(type=photo_type, visit=visit, creator=self.manager,
                                    link='https://example.test/' + suffix + '.jpg')

    def edit_url(self, photo):
        return f'/core/api/admin/photo_edit/{photo.pk}/?p={self.project.pk}'

    def test_photo_list_detail_and_type_stay_in_project(self):
        list_response = self.api.get(f'/core/api/admin/photo_list?p={self.project.pk}')
        self.assertEqual(list_response.status_code, 200, list_response.data)
        rows = list_response.data if isinstance(list_response.data, list) else list_response.data['results']
        self.assertEqual([row['id'] for row in rows], [self.own.pk])
        self.assertEqual(self.api.get(self.edit_url(self.own)).status_code, 200)
        self.assertEqual(self.api.get(self.edit_url(self.foreign)).status_code, 404)
        self.assertEqual(self.api.get(
            f'/core/api/admin/retrive_photo_type/{self.foreign.type_id}/?p={self.project.pk}'
        ).status_code, 404)

    def test_edit_and_soft_delete_cannot_change_file_or_foreign_photo(self):
        self.assertEqual(self.api.patch(self.edit_url(self.foreign),
                                        {'is_checked': True}, format='json').status_code, 404)
        self.assertEqual(self.api.delete(self.edit_url(self.foreign)).status_code, 404)
        self.assertEqual(self.api.patch(self.edit_url(self.own),
                                        {'link': 'https://example.test/replaced.jpg'},
                                        format='json').status_code, 400)
        self.own.refresh_from_db()
        self.assertTrue(self.own.link.endswith('ONE.jpg'))
        self.assertEqual(self.api.patch(self.edit_url(self.own),
                                        {'is_checked': True}, format='json').status_code, 200)
        self.own.refresh_from_db()
        self.assertTrue(self.own.is_checked)
        self.assertEqual(self.api.delete(self.edit_url(self.own)).status_code, 204)
        self.own.refresh_from_db()
        self.assertTrue(self.own.is_deleted)
        self.assertEqual(self.api.get(self.edit_url(self.own)).status_code, 404)
        self.foreign.refresh_from_db()
        self.assertFalse(self.foreign.is_deleted)
