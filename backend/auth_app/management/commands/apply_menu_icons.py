"""Preview or write the admin sidebar icon set into AdminMenu.active_icon / deactive_icon."""
from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from auth_app.menu_icons import icon_key, icons_for
from auth_app.models import AdminMenu


class Command(BaseCommand):
    help = 'Assign the shared line-icon set to admin menus by destination. Dry run unless --apply.'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int, help='Only menus of this project.')
        parser.add_argument('--only-empty', action='store_true', help='Keep icons that are already set.')
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        rows = AdminMenu.objects.all()
        if options['project']:
            rows = rows.filter(project_id=options['project'])
        if options['only_empty']:
            rows = rows.filter(active_icon__isnull=True) | rows.filter(active_icon='')
        groups = set(AdminMenu.objects.exclude(parent=None).values_list('parent_id', flat=True))
        plan = [(row, row.has_submenu or row.pk in groups) for row in rows.order_by('project_id', 'role_id', 'priority')]
        counts = Counter(icon_key(row.frontend_route_url, group) for row, group in plan)
        self.stdout.write(f'Menus: {len(plan)}; icons: ' + ', '.join(f'{key}={count}' for key, count in sorted(counts.items())))
        unmatched = sorted({row.frontend_route_url for row, group in plan if icon_key(row.frontend_route_url, group) == 'dot'})
        if unmatched:
            self.stdout.write('Generic icon for: ' + ', '.join(str(route) for route in unmatched))
        if not options['apply']:
            self.stdout.write('Preview only. Add --apply to write the icons.')
            return
        with transaction.atomic():
            for row, group in plan:
                row.active_icon, row.deactive_icon = icons_for(row.frontend_route_url, group)
                row.save(update_fields=['active_icon', 'deactive_icon'])
        self.stdout.write(self.style.SUCCESS(f'Icons written for {len(plan)} menus.'))
