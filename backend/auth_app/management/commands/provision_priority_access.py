"""Preview or provision service-priority grants and the admin menu for one project-wide role."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auth_app.menu_icons import icons_for
from auth_app.models import AdminMenu, Project, Role, RoleAssignment, RoleView, ViewMethod

READ = (('PriorityFactorListCreateView', 'GET'), ('PriorityEntityView', 'GET'), ('PriorityRankingView', 'GET'))
WRITE = (('PriorityFactorListCreateView', 'POST'), ('PriorityFactorDetailView', 'PUT'),
         ('PriorityFactorDetailView', 'DELETE'), ('PriorityEntityView', 'PUT'))
CAPABILITY = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'DELETE': 'can_delete'}


class Command(BaseCommand):
    help = 'Preview or provision priority scoring access (read, or --manage for weights) and the /priority menu.'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int, required=True)
        parser.add_argument('--role', type=int, required=True)
        parser.add_argument('--manage', action='store_true', help='Also allow editing factors, weights and choices.')
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--all-projects', action='store_true',
                            help='Acknowledge that role grants apply to every project assigning this role.')

    def handle(self, *args, **options):
        project = Project.objects.filter(pk=options['project'], is_active=True).first()
        role = Role.objects.filter(pk=options['role'], is_active=True, asset_scope='project').first()
        if not project or not role:
            raise CommandError('An active project and an active project-wide role are required.')
        projects = list(RoleAssignment.objects.filter(role=role, is_deleted=False).values_list('project_id', flat=True).distinct())
        if project.pk not in projects:
            raise CommandError('The role has no active assignment in the selected project.')
        if options['apply'] and len(projects) > 1 and not options['all_projects']:
            raise CommandError('This role is assigned to multiple projects; --all-projects acknowledges global grants.')
        endpoints = READ + (WRITE if options['manage'] else ())
        self.stdout.write(f'Project: {project.pk}; role: {role.pk}; assigned projects: {projects}')
        self.stdout.write('Grants: ' + ', '.join(f'{name}:{method}' for name, method in endpoints))
        self.stdout.write('Admin menu: /priority (اولویت‌بندی خدمات)')
        if not options['apply']:
            self.stdout.write('Preview only. Add --apply after reviewing the role scope.')
            return
        with transaction.atomic():
            for name, method in endpoints:
                view, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
                grant = RoleView.objects.filter(role=role, view_method_name=view).first() or RoleView(role=role, view_method_name=view)
                setattr(grant, CAPABILITY[method], True)
                grant.save()
            if not AdminMenu.objects.filter(project=project, role=role, frontend_route_url='/priority').exists():
                priority = (AdminMenu.objects.filter(project=project, role=role, parent=None)
                            .order_by('-priority').values_list('priority', flat=True).first() or 0) + 1
                active, inactive = icons_for('/priority')
                AdminMenu.objects.create(project=project, role=role, priority=priority, name='Service priority',
                                         verbose_name='اولویت‌بندی خدمات', frontend_route_name='priority',
                                         frontend_route_url='/priority', is_active=True,
                                         active_icon=active, deactive_icon=inactive)
        self.stdout.write(self.style.SUCCESS('Priority access and menu provisioned.'))
