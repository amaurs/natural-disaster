# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-03 13:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disasters', '0004_auto_20171003_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='gps',
            field=models.CharField(max_length=200),
        ),
    ]
