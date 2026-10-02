from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('wallet', '0069_invoice_request_key')]
    operations = [
        migrations.AddField(model_name='codeforwalletinvoice', name='failed_attempts',
                            field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name='codeforwalletinvoice', name='consumed_at',
                            field=models.DateTimeField(blank=True, null=True)),
    ]
