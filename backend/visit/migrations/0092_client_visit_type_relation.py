import logging

from django.db import migrations, models


logger = logging.getLogger(__name__)


def rename_legacy_join_indexes(apps, schema_editor, reverse=False):
    """PostgreSQL index names remain unchanged when its M2M table is renamed."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    old = 'visit_client_legacy_visits' if reverse else 'visit_client_visit_types'
    new = 'visit_client_visit_types' if reverse else 'visit_client_legacy_visits'
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() AND tablename = %s", ['visit_client_legacy_visits'])
        names = [row[0] for row in cursor.fetchall() if row[0].startswith(old)]
    for name in names:
        renamed = new + name[len(old):]
        schema_editor.execute('ALTER INDEX %s RENAME TO %s' % (
            schema_editor.quote_name(name), schema_editor.quote_name(renamed)))


def restore_legacy_join_indexes(apps, schema_editor):
    rename_legacy_join_indexes(apps, schema_editor, reverse=True)


def copy_legacy_visit_types(apps, schema_editor):
    client_model = apps.get_model('visit', 'Client')
    old_links = client_model._meta.get_field('legacy_visits').remote_field.through
    new_links = client_model._meta.get_field('visit_types').remote_field.through
    database = schema_editor.connection.alias
    batch = []
    copied = 0
    skipped = 0
    for link in old_links.objects.using(database).select_related('client', 'visit__type').iterator(chunk_size=1000):
        visit_type = link.visit.type
        if visit_type is None or link.client.project_id is None or visit_type.project_id != link.client.project_id:
            skipped += 1
            continue
        batch.append(new_links(client_id=link.client_id, visittype_id=visit_type.pk))
        if len(batch) >= 1000:
            new_links.objects.using(database).bulk_create(batch, ignore_conflicts=True)
            copied += len(batch)
            batch = []
    if batch:
        new_links.objects.using(database).bulk_create(batch, ignore_conflicts=True)
        copied += len(batch)
    logger.info('Client visit-type migration: %s valid links copied, %s retained only as legacy.', copied, skipped)


class Migration(migrations.Migration):
    dependencies = [
        ('visit', '0091_buildingclient_end_reason_buildingclient_ended_by_and_more'),
    ]

    operations = [
        migrations.RenameField(model_name='client', old_name='visit_types', new_name='legacy_visits'),
        migrations.RunPython(rename_legacy_join_indexes, restore_legacy_join_indexes),
        migrations.AlterField(
            model_name='client', name='legacy_visits',
            field=models.ManyToManyField(blank=True, related_name='legacy_client_links', to='visit.visit'),
        ),
        migrations.AddField(
            model_name='client', name='visit_types',
            field=models.ManyToManyField(blank=True, related_name='clients', to='visit.visittype'),
        ),
        migrations.RunPython(copy_legacy_visit_types, migrations.RunPython.noop),
    ]
