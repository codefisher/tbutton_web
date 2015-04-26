# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tbutton_votes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tbuttonrequest',
            name='poster_email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='tbuttonrequestcomment',
            name='poster_email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
    ]
