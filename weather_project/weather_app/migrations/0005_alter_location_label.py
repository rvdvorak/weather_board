# Generated by Django 3.2.5 on 2021-10-26 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather_app', '0004_rename_favorite_location_is_favorite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='label',
            field=models.CharField(max_length=100),
        ),
    ]
