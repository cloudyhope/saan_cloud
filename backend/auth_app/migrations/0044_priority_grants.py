from django.db import migrations

READ = ('PriorityFactorListCreateView', 'PriorityEntityView', 'PriorityRankingView')
WRITE = (('PriorityFactorListCreateView', 'POST', 'can_create'), ('PriorityFactorDetailView', 'PUT', 'can_update'),
         ('PriorityFactorDetailView', 'DELETE', 'can_delete'), ('PriorityEntityView', 'PUT', 'can_update'))


def grant_priority(apps, schema_editor):
    """Visit readers may see priorities; roles that edit buildings may configure and assign them."""
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias

    def roles(view_name, method, capability):
        return set(role_view.objects.using(alias).filter(
            view_method_name__view_name=view_name, view_method_name__method=method, role__asset_scope='project',
            **{capability: True}).values_list('role_id', flat=True))

    def grant(role_ids, name, method, capability):
        view, _ = view_method.objects.using(alias).get_or_create(view_name=name, method=method)
        for role_id in role_ids:
            if not role_view.objects.using(alias).filter(role_id=role_id, view_method_name_id=view.pk).exists():
                role_view.objects.using(alias).create(role_id=role_id, view_method_name_id=view.pk, **{capability: True})

    readers = roles('AdminVisitsListView', 'GET', 'can_view')
    editors = roles('BuildingEditsAPIView', 'PATCH', 'can_update') | roles('BuildingEditsAPIView', 'PUT', 'can_update')
    for name in READ:
        grant(readers | editors, name, 'GET', 'can_view')
    for name, method, capability in WRITE:
        grant(editors, name, method, capability)


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0043_admin_dashboard_grant'), ('visit', '0098_priority_scoring')]
    operations = [migrations.RunPython(grant_priority, migrations.RunPython.noop)]
