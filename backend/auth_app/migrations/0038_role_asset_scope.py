from django.db import migrations, models


def migrate_existing_roles(apps, schema_editor):
    role = apps.get_model('auth_app', 'Role')
    alias = schema_editor.connection.alias
    # Existing role abbreviations are only used to initialize explicit policy.
    for abbreviation, scope in (('M', 'project'), ('C', 'client'), ('P', 'assigned'),
                                ('F', 'supervised'), ('V', 'supervised')):
        role.objects.using(alias).filter(title_abbreviation=abbreviation).update(asset_scope=scope)


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0037_alter_roleassignment_user')]
    operations = [
        migrations.AddField(
            model_name='role', name='asset_scope',
            field=models.CharField(default='none', max_length=12, choices=[
                ('none', 'No asset access'), ('client', 'Client buildings'),
                ('assigned', 'Assigned visits'), ('supervised', 'Supervised visits'),
                ('project', 'All project assets'),
            ]),
        ),
        migrations.RunPython(migrate_existing_roles, migrations.RunPython.noop),
    ]
