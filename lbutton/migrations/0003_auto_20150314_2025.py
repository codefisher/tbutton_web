# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lbutton', '0002_auto_20150314_1805'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkButtonBuild',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('link_button', models.ForeignKey(to='lbutton.LinkButton', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='linkbutton',
            name='featured',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='linkbutton',
            name='downloads',
            field=models.IntegerField(default=0),
        ),
    ]
