# Generated by Django 2.2.10 on 2020-02-27 20:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('acct', '0003_preset_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='txn',
            options={'ordering': ['-id']},
        ),
    ]
