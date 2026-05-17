# import_export/migrations/0002_add_bank_statement_import.py
# Generated migration for bank statement import functionality

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),  # Ou a última migração de transactions
        ('import_export', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='importhistory',
            name='format',
        ),
        migrations.AddField(
            model_name='importhistory',
            name='bank',
            field=models.CharField(
                choices=[
                    ('bb', 'Banco do Brasil'),
                    ('itau', 'Itaú'),
                    ('nubank', 'Nubank'),
                    ('generic', 'Genérico'),
                ],
                default='generic',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='file_format',
            field=models.CharField(
                choices=[
                    ('csv', 'CSV'),
                    ('xlsx', 'Excel'),
                    ('pdf', 'PDF'),
                    ('ofx', 'OFX'),
                    ('bbt', 'BBT (Banco do Brasil)'),
                    ('txt', 'TXT'),
                    ('json', 'JSON'),
                ],
                default='csv',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='total_lines_read',
            field=models.IntegerField(default=0, help_text='Total de linhas/registros lidos do arquivo'),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='duplicates_ignored',
            field=models.IntegerField(default=0, help_text='Registros duplicados ignorados'),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='validation_errors',
            field=models.JSONField(blank=True, default=list, help_text='Lista de erros por linha'),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='period_start',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='period_end',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='importhistory',
            name='file_size',
            field=models.BigIntegerField(default=0, help_text='Tamanho do arquivo em bytes'),
        ),
        migrations.AlterField(
            model_name='importhistory',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pendente'),
                    ('processing', 'Processando'),
                    ('completed', 'Concluído'),
                    ('completed_with_errors', 'Concluído com Erros'),
                    ('failed', 'Falhou'),
                ],
                default='pending',
                max_length=30,
            ),
        ),
        migrations.AddIndex(
            model_name='importhistory',
            index=models.Index(fields=['user', '-created_at'], name='import_exp_user_id_created_idx'),
        ),
        migrations.AddIndex(
            model_name='importhistory',
            index=models.Index(fields=['user', 'status'], name='import_exp_user_id_status_idx'),
        ),
        migrations.CreateModel(
            name='TransactionImportMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fitid', models.CharField(blank=True, help_text='FITID do OFX ou identificador único do banco', max_length=255, null=True)),
                ('document_number', models.CharField(blank=True, help_text='Número do documento/lançamento', max_length=255, null=True)),
                ('transaction_type', models.CharField(
                    blank=True,
                    choices=[('credit', 'Crédito'), ('debit', 'Débito')],
                    max_length=20,
                )),
                ('previous_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('current_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('bank', models.CharField(blank=True, max_length=50)),
                ('account_number', models.CharField(blank=True, max_length=100, null=True)),
                ('raw_data', models.JSONField(blank=True, default=dict, help_text='Dados brutos originais do arquivo')),
                ('import_date', models.DateTimeField(auto_now_add=True)),
                ('import_history', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imported_transactions', to='import_export.importhistory')),
                ('transaction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='import_metadata', to='transactions.transaction')),
            ],
            options={
                'verbose_name': 'Metadados de Importação',
                'verbose_name_plural': 'Metadados de Importação',
            },
        ),
        migrations.AddIndex(
            model_name='transactionimportmetadata',
            index=models.Index(fields=['fitid'], name='import_exp_fitid_idx'),
        ),
        migrations.AddIndex(
            model_name='transactionimportmetadata',
            index=models.Index(fields=['document_number'], name='import_exp_document_idx'),
        ),
        migrations.AddIndex(
            model_name='transactionimportmetadata',
            index=models.Index(fields=['import_history'], name='import_exp_import_idx'),
        ),
    ]
