# Custom migration to make id_account the primary key

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_account_type'),
    ]

    operations = [
        # Step 1: Add id_account field as unique but not PK yet
        migrations.AddField(
            model_name='account',
            name='id_account',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        # Step 2: Run raw SQL to change primary key from id to id_account
        # This uses CASCADE to handle foreign keys
        migrations.RunSQL(
            sql="""
            ALTER TABLE accounts_account DROP CONSTRAINT accounts_account_pkey CASCADE;
            ALTER TABLE accounts_account ADD PRIMARY KEY (id_account);
            ALTER TABLE accounts_account DROP COLUMN id;
            """,
            reverse_sql="""
            ALTER TABLE accounts_account DROP CONSTRAINT accounts_account_pkey;
            ALTER TABLE accounts_account ADD COLUMN id BIGSERIAL PRIMARY KEY;
            ALTER TABLE accounts_account DROP CONSTRAINT accounts_account_id_account_key;
            """
        ),
    ]
