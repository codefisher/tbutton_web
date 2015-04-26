# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tbutton_votes', '0002_auto_20150426_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tbuttonrequest',
            name='subscriptions',
            field=models.ManyToManyField(related_name='tbutton_request_subscriptions', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
