from django.db import migrations


def grant_client_invoice_payment(apps, schema_editor):
    role_model = apps.get_model('auth_app', 'Role')
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias
    for role in role_model.objects.using(alias).filter(asset_scope='client').iterator():
        for name, method, capability in (
            ('WalletInvoiceClientRetrieveView', 'GET', 'can_view'),
            ('WalletInvoiceCodeRequestView', 'POST', 'can_create'),
            ('WalletInvoiceCodeValidateView', 'POST', 'can_create'),
            ('WalletReceiptRetrieve', 'GET', 'can_view'),
        ):
            view, _ = view_method.objects.using(alias).get_or_create(view_name=name, method=method)
            grant, _ = role_view.objects.using(alias).get_or_create(
                role_id=role.pk, view_method_name_id=view.pk)
            if not getattr(grant, capability):
                setattr(grant, capability, True)
                grant.save(update_fields=[capability])


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0040_expert_support_grants')]
    operations = [migrations.RunPython(grant_client_invoice_payment, migrations.RunPython.noop)]
