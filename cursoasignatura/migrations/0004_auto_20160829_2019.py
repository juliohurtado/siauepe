# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-30 01:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cursoasignatura', '0003_auto_20160829_2018'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cursoasignatura',
            unique_together=set([('asignatura', 'curso', 'periodo')]),
        ),
    ]
