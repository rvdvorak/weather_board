from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class Location(models.Model):
    label = models.CharField(max_length=100)
    latitude = models.FloatField(
        validators=[
            MinValueValidator(-90, message='Latitude out of range'),
            MaxValueValidator(90, message='Latitude out of range')])
    longitude = models.FloatField(
        validators=[
            MinValueValidator(-180, message='Longitude out of range'),
            MaxValueValidator(180, message='Longitude out of range')])
    is_favorite = models.BooleanField(default=False)
    date_last_showed = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.label
