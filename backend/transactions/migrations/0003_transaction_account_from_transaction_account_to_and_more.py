import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_transaction_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='account_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions_from', to='accounts.account'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='account_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions_to', to='accounts.account'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='transactionaccount',
            name='role',
            field=models.CharField(choices=[('source', 'Source Account'), ('destination', 'Destination Account')], default='source', max_length=20),
        ),
    ]
