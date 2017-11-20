# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-18 23:08
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requestsHandler', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userconfig',
            name='created_date',
        ),
        migrations.RemoveField(
            model_name='userconfig',
            name='text',
        ),
        migrations.RemoveField(
            model_name='userconfig',
            name='title',
        ),
        migrations.AddField(
            model_name='userconfig',
            name='config',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={'foo': 'bar'}),
        ),
        migrations.AddField(
            model_name='userconfig',
            name='user_hash',
            field=models.CharField(default='111', max_length=10, unique=True),
        ),
    ]
