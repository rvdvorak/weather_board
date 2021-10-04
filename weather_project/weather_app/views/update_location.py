from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
from weather_app.models import Location
from django.core.exceptions import ValidationError
import pprint

def update_location(request):
    #TODO Exceptions
    if request.method == 'POST':
        location_id = int(request.POST.get('id'))
        location = Location.objects.get(pk=location_id)
        location.favorite = request.POST.get('favorite')
        location.save()
        base_url = reverse('dashboard')
        query_string = urlencode({'id': location_id})
        uri = f'{base_url}?{query_string}'
        return redirect(uri)
    else:
        return redirect('dashboard')
