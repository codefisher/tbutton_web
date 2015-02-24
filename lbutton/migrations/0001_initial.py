# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tbutton_web.lbutton.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LinkButton',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extension_id', models.CharField(unique=True, max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('label', models.CharField(max_length=100)),
                ('tooltip', models.CharField(max_length=100)),
                ('url', models.TextField()),
                ('chrome_name', models.CharField(max_length=100)),
                ('icon_16', models.ImageField(upload_to=tbutton_web.lbutton.models.image_path)),
                ('icon_24', models.ImageField(upload_to=tbutton_web.lbutton.models.image_path)),
                ('icon_32', models.ImageField(upload_to=tbutton_web.lbutton.models.image_path)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LinkButtonDownload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('query_string', models.TextField()),
                ('link', models.TextField()),
                ('title', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
