"""The sidebar restructure: status tabs, hidden legacy entries, merged groups; preview first, idempotent."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from auth_app.models import AdminMenu, Project, Role

GROUPS = [
    ('مدیریت ویزیت‌ها', '/visitmanagment/lists', [
        ('تکمیل نشده', '/visitmanagment/notcompeletevisits'), ('تکمیل شده', '/visitmanagment/completeVisited'),
        ('تایید شده', '/visitmanagment/acceptedvisits'), ('لیست ویزیت‌ها', '/visitmanagment/lists'),
        ('انواع خدمت', '/visitmanagment/visit-types'), ('تخصیص هوشمند', '/assignment')]),
    ('نظارت', '/supervisionmanagment/lists', [
        ('لیست نظارت‌ها', '/supervisionmanagment/lists'), ('تکمیل شده', '/supervisionmanagment/completesupervision')]),
    ('برنامه روزانه', '/actionplan/listactionplan', [('ثبت برنامه جدید', '/actionplan/newaction'),
                                                     ('برنامه‌های فعال', '/actionplan/listactionplan')]),
    ('مدیریت رسانه', '/medialist/list', [('لیست رسانه‌ها', '/medialist/list'), ('ایجاد رسانه', '/medialist/create')]),
    ('مدیریت فایل', '/filemanagement/filelist', [('آپلود فایل', '/filemanagement/uploadfile'),
                                                  ('لیست فایل‌ها', '/filemanagement/filelist')]),
    ('اولویت‌بندی خدمات', '/priority', []),
    ('اعلان‌ها', '/notifications', []),
    ('فروشگاه‌ها', '/storemng/listall', []),
    ('داشبورد', '/dashboard', []),
]


class MenuRestructureTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Menu')
        self.role = Role.objects.create(title='Menu role', title_abbreviation='M', asset_scope='project')
        for priority, (title, url, children) in enumerate(GROUPS, 1):
            parent = AdminMenu.objects.create(project=self.project, role=self.role, priority=priority, verbose_name=title,
                                              frontend_route_url=url, has_submenu=bool(children), is_active=True)
            for order, (child_title, child_url) in enumerate(children, 1):
                AdminMenu.objects.create(project=self.project, role=self.role, parent=parent, priority=order,
                                         verbose_name=child_title, frontend_route_url=child_url, is_active=True)

    def run_command(self, *args):
        output = StringIO()
        call_command('restructure_admin_menu', '--project', self.project.pk, '--role', self.role.pk, *args, stdout=output)
        return output.getvalue()

    def active(self, url):
        return AdminMenu.objects.filter(role=self.role, frontend_route_url=url, is_active=True)

    def top(self):
        return list(AdminMenu.objects.filter(role=self.role, parent=None, is_active=True).order_by('priority', 'id')
                    .values_list('verbose_name', flat=True))

    def test_preview_changes_nothing(self):
        before = list(AdminMenu.objects.order_by('pk').values_list('pk', 'parent_id', 'is_active', 'frontend_route_params'))
        text = self.run_command()
        self.assertIn('Preview only', text)
        self.assertIn('tabs «مدیریت ویزیت‌ها»', text)
        self.assertNotIn('move «انواع خدمت»', text)  # the settings merge already takes it out of the tab group
        self.assertEqual(before, list(AdminMenu.objects.order_by('pk').values_list('pk', 'parent_id', 'is_active', 'frontend_route_params')))

    def test_apply_builds_tabs_hides_legacy_and_merges_groups(self):
        self.run_command('--apply')
        visits = AdminMenu.objects.get(role=self.role, verbose_name='مدیریت ویزیت‌ها', is_active=True)
        self.assertEqual(visits.frontend_route_params, {'display': 'tabs'})
        self.assertEqual(sorted(visits.parent_menu.filter(is_active=True).values_list('frontend_route_url', flat=True)),
                         sorted(['/visitmanagment/notcompeletevisits', '/visitmanagment/completeVisited',
                                 '/visitmanagment/acceptedvisits', '/visitmanagment/lists']))
        self.assertFalse(AdminMenu.objects.filter(role=self.role, is_active=True,
                                                  frontend_route_url__startswith='/supervisionmanagment').exists())
        self.assertFalse(self.active('/notifications').exists())
        self.assertFalse(self.active('/storemng/listall').exists())
        planning = AdminMenu.objects.get(role=self.role, name='mg-planning')
        self.assertEqual([row.frontend_route_url for row in planning.parent_menu.order_by('priority')],
                         ['/assignment', '/actionplan/newaction', '/actionplan/listactionplan'])
        content = AdminMenu.objects.get(role=self.role, name='mg-content')
        self.assertEqual(content.parent_menu.count(), 4)
        settings = AdminMenu.objects.get(role=self.role, name='mg-settings')
        self.assertEqual([row.frontend_route_url for row in settings.parent_menu.order_by('priority')],
                         ['/priority', '/visitmanagment/visit-types'])
        self.assertTrue(settings.active_icon.startswith('data:image/svg+xml'))
        self.assertEqual(self.top(), ['مدیریت ویزیت‌ها', 'برنامه‌ریزی', 'محتوا', 'قواعد و تنظیمات', 'داشبورد'])
        # Nothing is deleted: the retired group rows are still there, inactive.
        self.assertTrue(AdminMenu.objects.filter(role=self.role, verbose_name='مدیریت رسانه', is_active=False).exists())

    def test_apply_twice_is_stable(self):
        self.run_command('--apply')
        snapshot = list(AdminMenu.objects.order_by('pk').values_list('pk', 'parent_id', 'is_active', 'priority'))
        self.run_command('--apply')
        self.assertEqual(snapshot, list(AdminMenu.objects.order_by('pk').values_list('pk', 'parent_id', 'is_active', 'priority')))

    def test_options_keep_or_skip_parts(self):
        self.run_command('--apply', '--keep-supervision', '--keep-notifications', '--keep-stores', '--skip', 'content', '--skip', 'tabs')
        self.assertTrue(self.active('/supervisionmanagment/lists').exists())
        self.assertTrue(self.active('/notifications').exists())
        self.assertTrue(self.active('/storemng/listall').exists())
        self.assertFalse(AdminMenu.objects.filter(role=self.role, name='mg-content').exists())
        self.assertFalse(AdminMenu.objects.filter(role=self.role, verbose_name='مدیریت ویزیت‌ها',
                                                  frontend_route_params__isnull=False).exists())
        self.assertTrue(AdminMenu.objects.filter(role=self.role, name='mg-planning').exists())

    def test_non_status_children_leave_a_tab_group_when_not_merged(self):
        self.run_command('--apply', '--skip', 'settings', '--skip', 'planning')
        visits = AdminMenu.objects.get(role=self.role, verbose_name='مدیریت ویزیت‌ها', is_active=True)
        self.assertEqual(visits.frontend_route_params, {'display': 'tabs'})
        for url in ('/visitmanagment/visit-types', '/assignment'):
            self.assertIsNone(self.active(url).get().parent_id)  # evicted to the top level, still reachable

    def test_unknown_project_or_role_is_refused(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('restructure_admin_menu', '--project', 999999, stdout=StringIO())
        other = Role.objects.create(title='No menu', title_abbreviation='M', asset_scope='project')
        with self.assertRaises(CommandError):
            call_command('restructure_admin_menu', '--project', self.project.pk, '--role', other.pk, stdout=StringIO())
