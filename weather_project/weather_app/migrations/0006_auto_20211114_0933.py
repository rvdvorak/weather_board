# Generated by Django 3.2.5 on 2021-11-14 08:33

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather_app', '0005_alter_location_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(-90, message='Latitude out of range'), django.core.validators.MaxValueValidator(90, message='Latitude out of range')]),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(-180, message='Longitude out of range'), django.core.validators.MaxValueValidator(180, message='Longitude out of range')]),
        ),
    ]