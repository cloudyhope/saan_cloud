"""Physical part persistence and authorized CRUD regressions."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Product, ProductModel


class ProductPersistenceTests(TestCase):
    def test_create_and_update_part_preserve_identity_and_created_time(self):
        model = ProductModel.objects.create(name='Demo board', model_number='PN-LOCAL')
        part = Product.objects.create(model=model, serial_number='SN-LOCAL-1')
        self.assertIsNotNone(part.pk)
        self.assertIsNotNone(part.datetime_created)
        created = part.datetime_created
        changed = part.datetime_last_change
        part.status = 'received'
        part.save()
        part.refresh_from_db()
        self.assertEqual(part.datetime_created, created)
        self.assertGreaterEqual(part.datetime_last_change, changed)
        self.assertEqual(part.serial_number, 'SN-LOCAL-1')
        self.assertEqual(part.status, 'received')

    def test_same_model_can_have_distinct_physical_parts(self):
        model = ProductModel.objects.create(name='Demo board', model_number='PN-LOCAL')
        first = Product.objects.create(model=model, serial_number='SN-LOCAL-1')
        second = Product.objects.create(model=model, serial_number='SN-LOCAL-2')
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(Product.objects.filter(model=model).count(), 2)

    def test_authorized_create_and_edit_part_via_api(self):
        user = User.objects.create(username='local-asset-test')
        project = Project.objects.create(name='Assets test')
        role = Role.objects.create(title='Assets test', title_abbreviation='M', asset_scope='project')
        RoleAssignment.objects.create(user=user, project=project, role=role)
        for name, method in (('ProductListCreateAPIView', 'POST'), ('ProductEditsAPIView', 'PATCH')):
            vm = ViewMethod.objects.create(view_name=name, method=method)
            RoleView.objects.create(role=role, view_method_name=vm, can_create=method == 'POST', can_update=method == 'PATCH')
        model = ProductModel.objects.create(name='Demo board', model_number='PN-LOCAL', project=project)
        api = APIClient()
        api.force_authenticate(user)
        response = api.post(f'/api/visit/ProductListCreate/?p={project.pk}', {
            'model': model.pk, 'serial_number': 'SN-API-LOCAL',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        part = Product.objects.get(pk=response.data['id'])
        response = api.patch(f'/api/visit/ProductEdits/{part.pk}/?p={project.pk}', {'status': 'checked'}, format='json')
        self.assertEqual(response.status_code, 200)
        part.refresh_from_db()
        self.assertEqual(part.status, 'checked')
