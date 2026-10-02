from django.db import migrations

CAPABILITY = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'DELETE': 'can_delete'}

ENDPOINTS = (
    ('AssignmentOverviewView', 'GET'), ('AssignmentPlanView', 'GET'), ('AssignmentApplyView', 'POST'),
    ('AssignmentExpertView', 'PUT'), ('AssignmentTimeOffView', 'POST'), ('AssignmentTimeOffDetailView', 'DELETE'),
    ('AssignmentSkillListView', 'POST'), ('AssignmentSkillDetailView', 'PUT'), ('AssignmentSkillDetailView', 'DELETE'),
    ('AssignmentRequirementView', 'PUT'), ('AssignmentSettingView', 'PUT'),
)


def grant_assignment(apps, schema_editor):
    """Roles that may edit visits (project-wide planners) plan and assign workers; nobody else gets it."""
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias
    planners = set(role_view.objects.using(alias).filter(
        view_method_name__view_name='AdminUpdateVisitView', view_method_name__method__in=('PUT', 'PATCH'),
        role__asset_scope='project', can_update=True).values_list('role_id', flat=True))
    for name, method in ENDPOINTS:
        view, _ = view_method.objects.using(alias).get_or_create(view_name=name, method=method)
        for role_id in planners:
            row = role_view.objects.using(alias).filter(role_id=role_id, view_method_name_id=view.pk).first()
            if row is None:
                role_view.objects.using(alias).create(role_id=role_id, view_method_name_id=view.pk,
                                                      **{CAPABILITY[method]: True})
            elif not getattr(row, CAPABILITY[method]):
                setattr(row, CAPABILITY[method], True)
                row.save(update_fields=[CAPABILITY[method]])


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0045_field_operations_grants'), ('visit', '0100_expert_assignment')]
    operations = [migrations.RunPython(grant_assignment, migrations.RunPython.noop)]
