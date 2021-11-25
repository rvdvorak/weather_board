from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode
from weather_app.models import Location
from django.contrib.auth.models import User
import requests
import json
import pytz
import pickle  # Used for persisting sample data for tests
from django.template.response import TemplateResponse


def get_location_params(request):
    if request.method == 'GET':
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        label = request.GET.get('label')
    elif request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        label = request.POST.get('label')
    if latitude and longitude and label:
        return {
            'latitude': latitude,
            'longitude': longitude,
            'label': label}
    else:
        return {}


def get_location_history(user):
    if user.is_authenticated:
        location_history = Location.objects.filter(
            user=user).order_by('-date_last_showed')
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/location_history.pkl', 'wb') as file:
        #     pickle.dump(location_history, file)
        return location_history
    return None


def get_favorite_locations(user):
    if user.is_authenticated:
        favorite_locations = Location.objects.filter(
            user=user,
            is_favorite=True).order_by('-date_last_showed')
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/favorite_locations.pkl', 'wb') as file:
        #     pickle.dump(favorite_locations, file)
        return favorite_locations
    return None


def redirect_to_login(location_params=None):
    uri = reverse('login_user')
    if location_params:
        uri += f'?{urlencode(location_params)}'
    return redirect(uri)


def redirect_to_dashboard(location_params=None):
    uri = reverse('dashboard')
    if location_params:
        uri += f'?{urlencode(location_params)}'
    return redirect(uri)


def render_dashboard(request, location=None, weather=None, air_pollution=None, charts=None):
    return TemplateResponse(
        request,
        'weather_app/dashboard.html', {
            'location': location,
            'weather': weather,
            'air_pollution': air_pollution,
            'charts': charts,
            'location_history': get_location_history(request.user),
            'favorite_locations': get_favorite_locations(request.user)})
