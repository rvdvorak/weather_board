# Generated by Django 3.2.5 on 2021-10-03 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather_app', '0002_auto_20210923_1939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='date_last_showed',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='favorite',
            field=models.BooleanField(default=False),
        ),
    ]