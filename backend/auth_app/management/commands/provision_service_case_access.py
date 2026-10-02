"""Explicitly provision the warranty/repair workbench for a project-wide role."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from auth_app.models import AdminMenu, Project, Role, RoleAssignment, RoleView, ViewMethod


ENDPOINTS = (
    ('WarrantyContractListCreateView', 'GET'), ('WarrantyContractListCreateView', 'POST'),
    ('WarrantyEligibleProductsView', 'GET'),
    ('WarrantyClaimListCreateView', 'GET'), ('WarrantyClaimDecisionView', 'POST'),
    ('RepairCaseListCreateView', 'GET'), ('RepairCaseListCreateView', 'POST'),
    ('RepairCaseDetailView', 'GET'), ('RepairCaseTransitionView', 'POST'),
    ('RepairCaseMaterialView', 'GET'), ('RepairCaseMaterialView', 'POST'),
    ('RepairCaseLoanerView', 'GET'), ('RepairCaseLoanerView', 'POST'), ('ClientListCreateAPIView', 'GET'),
    ('ProductListCreateAPIView', 'GET'),
)


class Command(BaseCommand):
    help = 'Preview or provision warranty/repair grants and the admin menu for one project-wide role.'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int, required=True)
        parser.add_argument('--role', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--all-projects', action='store_true',
                            help='Acknowledge that role grants apply to every project assigning this role.')

    def handle(self, *args, **options):
        project = Project.objects.filter(pk=options['project']).first()
        role = Role.objects.filter(pk=options['role']).first()
        if not project or not role:
            raise CommandError('The selected project and role must exist.')
        if role.asset_scope != 'project' or not role.is_active:
            raise CommandError('Only an active project-scoped management role is eligible.')
        assigned_projects = list(RoleAssignment.objects.filter(
            role=role, is_deleted=False).values_list('project_id', flat=True).distinct())
        if project.pk not in assigned_projects:
            raise CommandError('The role has no active assignment in the selected project.')
        if len(assigned_projects) > 1 and options['apply'] and not options['all_projects']:
            raise CommandError('This role is assigned to multiple projects; --all-projects acknowledges global grants.')
        self.stdout.write(f'Project: {project.pk}; role: {role.pk}; assigned projects: {assigned_projects}')
        self.stdout.write('New grants: ' + ', '.join(f'{name}:{method}' for name, method in ENDPOINTS))
        self.stdout.write('Admin menu: /service-cases')
        if not options['apply']:
            self.stdout.write('Preview only. Add --apply after reviewing the role scope.')
            return
        with transaction.atomic():
            for name, method in ENDPOINTS:
                view_method = ViewMethod.objects.filter(view_name=name, method=method).first()
                if view_method is None:
                    view_method = ViewMethod.objects.create(view_name=name, method=method)
                grant = RoleView.objects.filter(role=role, view_method_name=view_method).first()
                if grant is None:
                    grant = RoleView(role=role, view_method_name=view_method)
                setattr(grant, 'can_view' if method == 'GET' else 'can_create', True)
                grant.save()
            menu = AdminMenu.objects.filter(project=project, role=role,
                                             frontend_route_url='/service-cases').first()
            if menu is None:
                priority = (AdminMenu.objects.filter(project=project, role=role, parent=None)
                            .order_by('-priority').values_list('priority', flat=True).first() or 0) + 1
                AdminMenu.objects.create(project=project, role=role, priority=priority,
                                         name='Service cases', verbose_name='گارانتی و تعمیرات',
                                         frontend_route_name='serviceCases', frontend_route_url='/service-cases',
                                         is_active=True)
        self.stdout.write(self.style.SUCCESS('Service case grants and menu provisioned.'))
