"""Preview and opt in a project manager to warehouse catalog and transfer writes."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod


ENDPOINTS = ('WareListCreateView', 'WareTransactionEzCreateView')


class Command(BaseCommand):
    help = 'Preview or grant warehouse opening/transfer permissions to one project-wide role.'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int, required=True)
        parser.add_argument('--role', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--all-projects', action='store_true',
                            help='Acknowledge that role grants apply to every project assigning this role.')

    def handle(self, *args, **options):
        project = Project.objects.filter(pk=options['project'], is_active=True).first()
        role = Role.objects.filter(pk=options['role'], is_active=True,
                                   asset_scope='project').first()
        if not project or not role:
            raise CommandError('An active project and project-wide role are required.')
        projects = list(RoleAssignment.objects.filter(role=role, is_deleted=False,
                                                     project__is_active=True).values_list(
                                                         'project_id', flat=True).distinct())
        if project.pk not in projects:
            raise CommandError('The role is not assigned to the selected project.')
        if options['apply'] and len(projects) > 1 and not options['all_projects']:
            raise CommandError('Role grants affect multiple projects; pass --all-projects after reviewing them.')
        self.stdout.write(f'Project: {project.pk}; role: {role.pk}; assigned projects: {projects}')
        self.stdout.write('POST grants: ' + ', '.join(ENDPOINTS))
        self.stdout.write('The atomic opening endpoint requires both grants; it has no separate grant.')
        if not options['apply']:
            self.stdout.write('Preview only. Add --apply to provision.')
            return
        with transaction.atomic():
            for name in ENDPOINTS:
                method, _ = ViewMethod.objects.get_or_create(view_name=name, method='POST')
                grant, _ = RoleView.objects.get_or_create(role=role, view_method_name=method)
                if not grant.can_create:
                    grant.can_create = True
                    grant.save(update_fields=['can_create'])
        self.stdout.write(self.style.SUCCESS('Warehouse write grants provisioned.'))
