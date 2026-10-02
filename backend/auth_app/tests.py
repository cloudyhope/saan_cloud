from django.test import TestCase, SimpleTestCase
from core.urls import project_urlpatterns
from auth_app.models import *
from auth_app.views import *
from django.test import RequestFactory
from core.server import get_view_instance
from django.urls import resolve, reverse
import importlib
import sys
# from auth_app.views import *

# Create your tests here.


class TestUrls(SimpleTestCase):
    def check_one(self, url):
        self.assertEqual(resolve(reverse(url.pattern.name)).url_name, url.pattern.name)

    def test_resolve_all(self):
        # assert 1==2
        for url in project_urlpatterns:
            # print(url.lookup_str.split('.'+url.pattern.name)[0], url.pattern.name)
            if url.pattern.name and '<' not in str(url.pattern.regex):
                setattr(self, 'test_' + url.pattern.name, self.check_one(url))
            # x= resolve(reverse(url.pattern.name))
            # importlib.import_module(url.lookup_str.split('.'+url.pattern.name)[0], url.pattern.name) 
            # self.assertEquals(resolve(reverse(url.pattern.name)).func.view_class, globals()[url.pattern.name])


class TestViews(TestCase):
    def check_one(self, url):
        response = self.client.get(url.pattern.describe().split("'")[1])
        self.assertNotEqual(response.status_code, 500)
        self.assertNotEqual(response.status_code, 501)
        self.assertNotEqual(response.status_code, 502)
        self.assertNotEqual(response.status_code, 503)
        self.assertNotEqual(response.status_code, 504)
        self.assertNotEqual(response.status_code, 505)
        # importlib.import_module(url.lookup_str.split('.'+url.pattern.name)[0], url.pattern.name) 
        # self.assertEquals(resolve(reverse(url.pattern.name)).func.view_class, getattr(importlib.import_module(url.lookup_str.split('.'+url.pattern.name)[0]), url.pattern.name))
        print("PASSED")

    def test_resolve_all(self):
        # assert 1==2
        for url in project_urlpatterns:
            # print(url.lookup_str.split('.'+url.pattern.name)[0], url.pattern.name)
            if url.pattern.name and '<' not in str(url.pattern.regex):
                setattr(self, 'test_' + url.pattern.name, self.check_one(url))
            # x= resolve(reverse(url.pattern.name))
            # importlib.import_module(url.lookup_str.split('.'+url.pattern.name)[0], url.pattern.name) 
            # self.assertEquals(resolve(reverse(url.pattern.name)).func.view_class, globals()[url.pattern.name])



    # User with higher role can assign a role to a user with lower role in the same project

class TestUserPermissions(TestCase):

    def test_update_role_of_user_with_lower_role(self):
        # Create a user with a higher role
        view = get_view_instance("UserManagementView")
        higher_role_user = User.objects.create_user(username='higher_role_user', password='password')
        higher_role = Role.objects.create(title='Higher Role', priority=2)
        higher_role_assignment = RoleAssignment.objects.create(user=higher_role_user, role=higher_role)

        # Create a user with a lower role
        lower_role_user = User.objects.create_user(username='lower_role_user', password='password')
        lower_role = Role.objects.create(title='Lower Role', priority=1)
        lower_role_assignment = RoleAssignment.objects.create(user=lower_role_user, role=lower_role)

        # Create a project
        project = Project.objects.create(name='Project')

        # Update the role of the lower role user by the higher role user
        view.request = RequestFactory().post('/api/assign-role/', data={
            'project': project.id,
            'role': higher_role.id,
            'user': {
                'username': lower_role_user.username,
                'password': lower_role_user.password,
                'email': lower_role_user.email,
                'first_name': lower_role_user.first_name,
                'last_name': lower_role_user.last_name,
                'extended': {
                    'national_code': '1234567890',
                    'city': 1
                }
            },
            'change_password': False
        })
        response = view.post(view.request)

        # Assert that the role assignment was updated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
