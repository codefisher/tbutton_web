# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-23 08:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lbutton', '0004_auto_20170823_0029'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkbutton',
            name='version',
            field=models.IntegerField(default=1),
        ),
    ]
