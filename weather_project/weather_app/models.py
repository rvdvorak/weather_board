from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def validate_latitude(latitude):
    if not (-90.0 <= latitude <= 90.0):
        raise ValidationError(
            'Latitude out of range.',
            code='invalid',
            params={'latitude': latitude})

def validate_longitude(longitude):
    if not (-180.0 <= longitude <= 180.0):
        raise ValidationError(
            'Longitude out of range.',
            code='invalid',
            params={'longitude': longitude})


class Location(models.Model):
    label = models.CharField(max_length=100)
    latitude = models.FloatField(validators=[validate_latitude])
    longitude = models.FloatField(validators=[validate_longitude])
    is_favorite = models.BooleanField(default=False)
    date_last_showed = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.label