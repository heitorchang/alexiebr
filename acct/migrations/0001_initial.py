# Generated by Django 2.2.10 on 2020-02-27 18:27

import datetime
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Acct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=127)),
                ('budget', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=22)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='AcctType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=63)),
                ('sign', models.IntegerField()),
                ('order', models.IntegerField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Txn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('desc', models.CharField(max_length=127)),
                ('amt', models.DecimalField(decimal_places=2, max_digits=22)),
                ('credit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_txns', to='acct.Acct')),
                ('debit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debit_txns', to='acct.Acct')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', '-id'],
            },
        ),
        migrations.AddField(
            model_name='acct',
            name='acctType',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='acct.AcctType'),
        ),
        migrations.AddField(
            model_name='acct',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]