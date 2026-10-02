from django.db import migrations, models
import django.db.models.deletion


def assign_existing_assets(apps, schema_editor):
    alias = schema_editor.connection.alias
    project = apps.get_model('auth_app', 'Project')
    models_by_name = {name: apps.get_model('visit', name) for name in (
        'Building', 'Client', 'Elevator', 'Product', 'ProductModel',
    )}
    project_ids = list(project.objects.using(alias).values_list('pk', flat=True))
    if len(project_ids) == 1:
        # The legacy global database has one unambiguous project, including inactive ones.
        for model in models_by_name.values():
            model.objects.using(alias).filter(project__isnull=True).update(project_id=project_ids[0])
        return

    # With multiple projects, use existing relationships only when they agree.
    # Ambiguous/unlinked rows remain unassigned and unavailable in public asset APIs.
    def assign(name, pairs):
        candidates = {}
        for asset_id, project_id in pairs:
            if asset_id and project_id:
                candidates.setdefault(asset_id, set()).add(project_id)
        for asset_id, projects in candidates.items():
            if len(projects) == 1:
                models_by_name[name].objects.using(alias).filter(pk=asset_id, project__isnull=True).update(
                    project_id=next(iter(projects)))

    visit = apps.get_model('visit', 'Visit')
    assignment = apps.get_model('auth_app', 'RoleAssignment')
    user_client = apps.get_model('visit', 'UserClient')
    building_client = apps.get_model('visit', 'BuildingClient')
    building_elevator = apps.get_model('visit', 'BuildingElevator')
    product_elevator = apps.get_model('visit', 'ProductElevator')
    user_projects = {}
    for user_id, project_id in assignment.objects.using(alias).filter(is_deleted=False).values_list('user_id', 'project_id'):
        if project_id:
            user_projects.setdefault(user_id, set()).add(project_id)
    assign('Client', ((client_id, p) for client_id, user_id in user_client.objects.using(alias).values_list('client_id', 'user_id')
                      for p in user_projects.get(user_id, set())))
    from itertools import chain
    assign('Building', chain(
        visit.objects.using(alias).values_list('building_id', 'type__project_id'),
        building_client.objects.using(alias).values_list('building_id', 'client__project_id'),
    ))
    assign('Elevator', building_elevator.objects.using(alias).values_list('elevator_id', 'building__project_id'))
    assign('Product', product_elevator.objects.using(alias).values_list('product_id', 'elevator__project_id'))
    assign('ProductModel', models_by_name['Product'].objects.using(alias).values_list('model_id', 'project_id'))


class Migration(migrations.Migration):
    dependencies = [('visit', '0087_store_records'), ('auth_app', '0038_role_asset_scope')]
    operations = [
        migrations.AddField(
            model_name=name, name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    to='auth_app.project'),
        ) for name in ('client', 'building', 'elevator', 'product', 'productmodel')
    ] + [migrations.RunPython(assign_existing_assets, migrations.RunPython.noop)]
