from django.db import migrations


def grant_dashboard(apps, schema_editor):
    """Project-wide roles that already list visits may read the management dashboard."""
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias
    roles = role_view.objects.using(alias).filter(
        view_method_name__view_name='AdminVisitsListView', view_method_name__method='GET', can_view=True,
        role__asset_scope='project',
    ).values_list('role_id', flat=True).distinct()
    view, _ = view_method.objects.using(alias).get_or_create(view_name='AdminDashboardView', method='GET')
    for role_id in roles:
        if not role_view.objects.using(alias).filter(role_id=role_id, view_method_name_id=view.pk).exists():
            role_view.objects.using(alias).create(role_id=role_id, view_method_name_id=view.pk, can_view=True)


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0042_client_wallet_balance_grant')]
    operations = [migrations.RunPython(grant_dashboard, migrations.RunPython.noop)]
