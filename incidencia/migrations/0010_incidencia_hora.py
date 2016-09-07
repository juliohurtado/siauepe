# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-09-07 15:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horario', '0003_auto_20160906_1153'),
        ('incidencia', '0009_auto_20160906_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='incidencia',
            name='hora',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='horario.Horario'),
            preserve_default=False,
        ),
    ]
