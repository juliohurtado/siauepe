# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-20 15:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curso', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='especialidad',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
