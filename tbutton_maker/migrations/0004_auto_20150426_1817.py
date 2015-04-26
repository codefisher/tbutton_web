# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tbutton_maker', '0003_auto_20141019_2048'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('query_string', models.TextField()),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='downloadsession',
            name='ip_address',
            field=models.GenericIPAddressField(null=True),
        ),
        migrations.AddField(
            model_name='downloadsession',
            name='user_agent',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
