from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from urllib.parse import urlencode
from weather_app.models import Location
import requests
import json
import pytz
import pickle  # Used for persisting sample data for tests


def get_view_mode(request):
    valid_modes = ['48h_detail', '7d_detail']
    if request.method == 'GET':
        view_mode = request.GET.get('view_mode')
    elif request.method == 'POST':
        view_mode = request.POST.get('view_mode')
    if view_mode in valid_modes:
        return view_mode
    else:
        return valid_modes[0]

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


def redirect_to_dashboard(location_params={}, view_mode=None):
    base_url = reverse('dashboard')
    query = {'view_mode': view_mode, **location_params}    
    query_string = urlencode(query)
    uri = f'{base_url}?{query_string}'
    return redirect(uri)


def render_dashboard(request, location=None, weather=None, air_pollution=None, charts=None):
    if get_messages(request):
        return TemplateResponse(
            request,
            'weather_app/messages.html', {
                'view_mode': get_view_mode(request),
                'location_history': get_location_history(request.user),
                'favorite_locations': get_favorite_locations(request.user),
                'view_mode': get_view_mode(request)})
    elif location and weather and air_pollution and charts:
        return TemplateResponse(
            request,
            'weather_app/dashboard.html', {
                'view_mode': get_view_mode(request),
                'location': location,
                'weather': weather,
                'air_pollution': air_pollution,
                'charts': charts,
                'location_history': get_location_history(request.user),
                'favorite_locations': get_favorite_locations(request.user),
                'view_mode': get_view_mode(request)})
    else:
        return TemplateResponse(
            request,
            'weather_app/no_location.html', {
                'view_mode': get_view_mode(request),
                'location_history': get_location_history(request.user),
                'favorite_locations': get_favorite_locations(request.user),
                'view_mode': get_view_mode(request)})
        

