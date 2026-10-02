"""Action-plan spreadsheet parsing is private, bounded and predictable."""
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod


class ActionPlanImportTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Import local')
        self.user = User.objects.create(username='import-manager')
        self.role = Role.objects.create(title='Import manager', title_abbreviation='I',
                                        asset_scope='project')
        RoleAssignment.objects.create(user=self.user, role=self.role, project=self.project)
        method, _ = ViewMethod.objects.get_or_create(view_name='AdminActionPlanCreate', method='POST')
        RoleView.objects.create(role=self.role, view_method_name=method, can_create=True)
        self.api = APIClient()
        self.url = f'/config/parse_excel/?p={self.project.pk}'

    def upload(self, content, name='plan.csv'):
        return self.api.post(self.url, {'file': SimpleUploadedFile(name, content)},
                             format='multipart')

    def test_import_requires_active_authorized_project_role(self):
        content = b'building_code,expert_phone_number\nA-1,09120000000\n'
        self.assertIn(self.upload(content).status_code, (401, 403))
        self.api.force_authenticate(self.user)
        self.assertEqual(self.upload(content).status_code, 200)
        self.assertEqual(self.upload(content).data['data'][0]['building_code'], 'A-1')
        RoleAssignment.objects.filter(user=self.user).update(is_deleted=True)
        self.assertEqual(self.upload(content).status_code, 403)

    def test_import_validates_headers_rows_size_and_types(self):
        self.api.force_authenticate(self.user)
        valid = ('outlet_code,promoter_phone_number,elevator_ids\n'
                 'A-1,9120000000,"1;2"\n').encode()
        self.assertEqual(self.upload(valid).data['data'][0], {
            'building_code': 'A-1', 'expert_phone_number': '09120000000',
            'elevator_ids': [1, 2], 'source_row': 2,
        })
        for content, name in ((b'x,y\na,b\n', 'bad.csv'),
                              (b'building_code,expert_phone_number\nA-1,\n', 'bad.csv'),
                              (b'building_code,expert_phone_number,elevator_ids\nA-1,0912,1;1\n', 'bad.csv'),
                              (b'not a workbook', 'bad.xlsx'),
                              (b'x' * (2 * 1024 * 1024 + 1), 'large.csv')):
            with self.subTest(name=name, size=len(content)):
                self.assertEqual(self.upload(content, name).status_code, 400)
