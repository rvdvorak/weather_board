from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    label = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    favourite = models.BooleanField()
    date_last_showed = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.label