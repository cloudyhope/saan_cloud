from django.db import migrations


def grant_wallet_balance(apps, schema_editor):
    role_model = apps.get_model('auth_app', 'Role')
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias
    view, _ = view_method.objects.using(alias).get_or_create(view_name='WalletGetSignatureView', method='GET')
    for role in role_model.objects.using(alias).filter(asset_scope='client').iterator():
        grant, _ = role_view.objects.using(alias).get_or_create(role_id=role.pk, view_method_name_id=view.pk)
        if not grant.can_view:
            grant.can_view = True
            grant.save(update_fields=['can_view'])


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0041_client_invoice_payment_grants')]
    operations = [migrations.RunPython(grant_wallet_balance, migrations.RunPython.noop)]
