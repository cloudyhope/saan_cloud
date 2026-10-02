from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('wallet', '0070_invoice_code_lifecycle')]
    operations = [
        migrations.RemoveField(model_name='codeforwalletinvoice', name='code'),
        migrations.AddField(model_name='codeforwalletinvoice', name='code_hash',
                            field=models.CharField(blank=True, max_length=128)),
    ]
