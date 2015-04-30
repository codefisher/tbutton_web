# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tbutton_maker', '0004_auto_20150426_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='updatesession',
            name='ip_address',
            field=models.GenericIPAddressField(null=True),
        ),
        migrations.AlterField(
            model_name='updatesession',
            name='user_agent',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
