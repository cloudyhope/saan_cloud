from django.test import TestCase, SimpleTestCase
from django.urls import resolve, reverse
# from auth_app.views import *
import importlib
import sys
# Create your tests here.

from core.urls import project_urlpatterns

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

