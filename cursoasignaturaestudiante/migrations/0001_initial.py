# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-10 20:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cursoasignatura', '0001_initial'),
        ('estudiante', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CursoAsignaturaEstudiante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asignatura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cursoasignatura.CursoAsignatura')),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estudiante.Estudiante')),
            ],
        ),
    ]
