from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('wallet', '0068_remove_walletinvoice_buyer_and_more')]
    operations = [
        migrations.AddField(model_name='walletinvoice', name='request_key',
                            field=models.UUIDField(blank=True, null=True)),
        migrations.AddField(model_name='walletinvoice', name='payload_hash',
                            field=models.CharField(blank=True, default='', max_length=64)),
        migrations.AddConstraint(model_name='walletinvoice', constraint=models.UniqueConstraint(
            fields=('expert', 'request_key'), condition=models.Q(request_key__isnull=False),
            name='invoice_expert_request_key_unique')),
    ]
