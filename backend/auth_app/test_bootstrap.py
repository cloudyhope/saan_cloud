"""First-run bootstrap of a fresh production database."""
import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from auth_app.models import AdminMenu, ExtendedUser, Project, Role, RoleAssignment, RoleView
from config.models import NavMenu

STRONG = 'Zq7-long-and-unusual-passphrase'


class BootstrapTests(TestCase):
    def run_command(self, *args, password=STRONG):
        env = {'BOOTSTRAP_ADMIN_PASSWORD': password} if password is not None else {}
        with mock.patch.dict(os.environ, env, clear=False):
            if password is None:
                os.environ.pop('BOOTSTRAP_ADMIN_PASSWORD', None)
            out = StringIO()
            call_command('bootstrap_saan', '--admin-phone', '09120000000', '--admin-name', 'Owner Name', *args, stdout=out)
        return out.getvalue()

    def test_creates_project_roles_grants_menus_and_a_superuser(self):
        text = self.run_command()
        self.assertNotIn(STRONG, text)  # the password is never printed
        project = Project.objects.get(name='saanapp')
        self.assertEqual(set(Role.objects.values_list('title', flat=True)),
                         {'Admin', 'Planner', 'Support', 'Warehouse', 'Expert', 'Client', 'ClientRep'})
        admin_role = Role.objects.get(title='Admin')
        self.assertGreater(RoleView.objects.filter(role=admin_role).count(), 200)
        # Each role gets the grants of its screens and no more.
        expert = RoleView.objects.filter(role=Role.objects.get(title='Expert'), view_method_name__view_name='PromoterVisitsAPIView')
        self.assertTrue(expert.exists())
        self.assertFalse(RoleView.objects.filter(role=Role.objects.get(title='Expert'),
                                                 view_method_name__view_name='AssignmentApplyView').exists())
        self.assertTrue(RoleView.objects.filter(role=Role.objects.get(title='Planner'),
                                                view_method_name__view_name='AssignmentApplyView').exists())
        client_views = set(RoleView.objects.filter(role=Role.objects.get(title='ClientRep'),
                                                   can_create=True).values_list('view_method_name__view_name', flat=True))
        self.assertEqual(client_views, set())  # read-only representative
        user = User.objects.get(username='09120000000')
        self.assertTrue(user.check_password(STRONG))
        self.assertTrue(user.is_superuser and user.is_staff)
        self.assertEqual(ExtendedUser.objects.get(user=user).role, 'M')
        self.assertTrue(RoleAssignment.objects.filter(user=user, role=admin_role, project=project).exists())
        # Admin menu: shortened layout with status tabs; field menus per role.
        top = list(AdminMenu.objects.filter(role=admin_role, project=project, parent=None, is_active=True)
                   .order_by('priority').values_list('verbose_name', flat=True))
        self.assertIn('مدیریت ویزیت‌ها', top)
        self.assertNotIn('فروشگاه‌ها', top)
        self.assertNotIn('نظارت', top)
        visits = AdminMenu.objects.get(role=admin_role, project=project, verbose_name='مدیریت ویزیت‌ها', is_active=True)
        self.assertEqual(visits.frontend_route_params, {'display': 'tabs'})
        self.assertEqual(list(NavMenu.objects.filter(role=Role.objects.get(title='Expert')).order_by('priority')
                              .values_list('route', flat=True))[:2], ['tasks', 'wares'])
        self.assertTrue(NavMenu.objects.filter(role=Role.objects.get(title='Client'), is_landing=True, route='home').exists())

    def test_rerun_keeps_everything_a_person_changed(self):
        self.run_command()
        planner = Role.objects.get(title='Planner')
        RoleView.objects.filter(role=planner, view_method_name__view_name='AssignmentApplyView').delete()
        AdminMenu.objects.filter(role=planner).update(is_active=False)
        self.run_command(password='A-different-passphrase-9')
        self.assertFalse(RoleView.objects.filter(role=planner, view_method_name__view_name='AssignmentApplyView').exists())
        self.assertFalse(AdminMenu.objects.filter(role=planner, is_active=True).exists())
        self.assertTrue(User.objects.get(username='09120000000').check_password(STRONG))  # password untouched
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Role.objects.count(), 7)
        # Explicit refresh rewrites them.
        self.run_command('--refresh-grants', '--refresh-menus')
        self.assertTrue(RoleView.objects.filter(role=planner, view_method_name__view_name='AssignmentApplyView').exists())
        self.assertTrue(AdminMenu.objects.filter(role=planner, is_active=True).exists())

    def test_password_rules_and_input_checks(self):
        with self.assertRaises(CommandError):
            self.run_command(password='12345678')  # too common / numeric
        with self.assertRaises(CommandError):
            self.run_command(password=None)  # no password available, not interactive
        with self.assertRaises(CommandError):
            call_command('bootstrap_saan', '--admin-phone', 'not-a-phone', stdout=StringIO())
        self.assertFalse(User.objects.exists())
        self.assertFalse(Role.objects.exists())  # a refused run changes nothing
