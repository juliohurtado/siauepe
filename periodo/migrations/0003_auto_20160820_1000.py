# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-20 15:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('periodo', '0002_auto_20160701_1315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='periodo',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]