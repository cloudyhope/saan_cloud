"""Preview or add the admin menu rows of the field-operations package for one role.

Grants come from migration auth_app.0045; this only places the two new pages in the role's
existing sidebar, under the matching group when the role has one.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auth_app.menu_icons import icons_for
from auth_app.models import AdminMenu, Project, Role, RoleAssignment

# (route, route name, menu name, title, parent group's route or None for the top level; run
# `restructure_admin_menu` afterwards to file top-level pages into the merged groups)
ITEMS = (
    ('/warehouse/part-requests', 'partRequests', 'Part requests', 'درخواست‌های قطعه', '/warehouse/warelist'),
    ('/visitmanagment/visit-types', 'visitTypes', 'Service types', 'انواع خدمت', None),
    ('/assignment', 'assignment', 'Smart assignment', 'تخصیص هوشمند', None),
)


class Command(BaseCommand):
    help = 'Preview or add the part-request and service-type admin menus for one project role.'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int, required=True)
        parser.add_argument('--role', type=int, required=True)
        parser.add_argument('--only', choices=[item[0] for item in ITEMS], help='Add just this route.')
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        project = Project.objects.filter(pk=options['project'], is_active=True).first()
        role = Role.objects.filter(pk=options['role'], is_active=True, asset_scope='project').first()
        if not project or not role:
            raise CommandError('An active project and an active project-wide role are required.')
        if not RoleAssignment.objects.filter(role=role, project=project, is_deleted=False).exists():
            raise CommandError('The role has no active assignment in the selected project.')
        items = [item for item in ITEMS if not options['only'] or item[0] == options['only']]
        plan = []
        for route, route_name, name, title, group_route in items:
            if AdminMenu.objects.filter(project=project, role=role, frontend_route_url=route).exists():
                self.stdout.write(f'{route}: already in the menu')
                continue
            group = (AdminMenu.objects.filter(project=project, role=role, parent=None, frontend_route_url=group_route).first()
                     if group_route else None)
            plan.append((route, route_name, name, title, group))
            self.stdout.write(f'{route}: add «{title}» ' + (f'under menu {group.pk}' if group else 'at the top level'))
        if not options['apply']:
            self.stdout.write('Preview only. Add --apply to create the rows.')
            return
        with transaction.atomic():
            for route, route_name, name, title, group in plan:
                siblings = AdminMenu.objects.filter(project=project, role=role, parent=group)
                priority = (siblings.order_by('-priority').values_list('priority', flat=True).first() or 0) + 1
                active, inactive = icons_for(route)
                AdminMenu.objects.create(project=project, role=role, parent=group, priority=priority, name=name,
                                         verbose_name=title, frontend_route_name=route_name, frontend_route_url=route,
                                         is_active=True, active_icon=active, deactive_icon=inactive)
                if group and not group.has_submenu:
                    group.has_submenu = True
                    group.save(update_fields=['has_submenu'])
        self.stdout.write(self.style.SUCCESS(f'{len(plan)} menu row(s) added.'))
