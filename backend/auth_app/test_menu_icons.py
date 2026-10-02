"""Sidebar icons are written into the existing AdminMenu icon fields."""
from io import StringIO
from urllib.parse import unquote

from django.core.management import call_command
from django.test import TestCase

from auth_app.menu_icons import icon_key, icons_for
from auth_app.models import AdminMenu, Project, Role


class MenuIconTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Icons')
        self.role = Role.objects.create(title='Icons', title_abbreviation='M', asset_scope='project')

    def menu(self, url, parent=None, icon=None):
        return AdminMenu.objects.create(project=self.project, role=self.role, priority=1, frontend_route_url=url,
                                        parent=parent, has_submenu=False, active_icon=icon, deactive_icon=icon)

    def test_routes_groups_and_unknown_destinations(self):
        self.assertEqual(icon_key('/visitmanagment/lists'), 'list')
        self.assertEqual(icon_key('/Ticket/ticketList/'), 'messages')
        self.assertEqual(icon_key('/visitmanagment/lists', is_group=True), 'clipboard-check')
        self.assertEqual(icon_key('/pic/visitpic/1379'), 'camera')
        self.assertEqual(icon_key('/something-new'), 'dot')
        active, inactive = icons_for('/dashboard')
        self.assertTrue(active.startswith('data:image/svg+xml'))
        self.assertIn('stroke="#ffffff"', unquote(active))
        self.assertIn('stroke="#9fb0cc"', unquote(inactive))

    def test_command_previews_then_applies(self):
        group = self.menu('/warehouse/warelist')
        child = self.menu('/warehouse/create', parent=group)
        kept = self.menu('/dashboard', icon='https://cdn.example/icon.svg')
        call_command('apply_menu_icons', stdout=StringIO())
        group.refresh_from_db()
        self.assertIsNone(group.active_icon)  # preview writes nothing
        call_command('apply_menu_icons', '--apply', '--only-empty', stdout=StringIO())
        group.refresh_from_db(); child.refresh_from_db(); kept.refresh_from_db()
        self.assertIn('M12 3l8 4.5', unquote(group.active_icon))  # warehouse group → package
        self.assertTrue(child.deactive_icon.startswith('data:image/svg+xml'))
        self.assertEqual(kept.active_icon, 'https://cdn.example/icon.svg')
        call_command('apply_menu_icons', '--apply', stdout=StringIO())
        kept.refresh_from_db()
        self.assertTrue(kept.active_icon.startswith('data:image/svg+xml'))
