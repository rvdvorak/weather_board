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


def get_query(request):
    valid_modes = ['48h_detail', '7d_detail']
    query = {}
    if request.method == 'GET':
        query['display_mode'] = request.GET.get('display_mode')
        query['label'] = request.GET.get('label') or ''
        query['latitude'] = request.GET.get('latitude') or ''
        query['longitude'] = request.GET.get('longitude') or ''
    elif request.method == 'POST':
        query['display_mode'] = request.POST.get('display_mode')
        query['label'] = request.POST.get('label') or ''
        query['latitude'] = request.POST.get('latitude') or ''
        query['longitude'] = request.POST.get('longitude') or ''
    if not query['display_mode'] in valid_modes:
        query['display_mode'] = valid_modes[0]
    return query


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


def redirect_to_dashboard(query):
    base_url = reverse('dashboard')
    query_string = urlencode(query)
    uri = f'{base_url}?{query_string}'
    return redirect(uri)


def render_dashboard(request, location=None, weather=None, air_pollution=None, charts=None):
    query = get_query(request)
    location_history = get_location_history(request.user)
    favorite_locations = get_favorite_locations(request.user)
    if get_messages(request):
        # Show messages
        return TemplateResponse(
            request,
            'weather_app/messages.html', {
                'query': query,
                'location': None,
                'weather': None,
                'air_pollution': None,
                'charts': None,
                'location_history': location_history,
                'favorite_locations': favorite_locations})
    elif location and weather and air_pollution and charts:
        # Show weather forecast
        return TemplateResponse(
            request,
            'weather_app/dashboard.html', {
                'query': {
                    'display_mode': query['display_mode'],
                    'label': location.label,
                    'latitude': location.latitude,
                    'longitude': location.longitude},
                'location': location,
                'weather': weather,
                'air_pollution': air_pollution,
                'charts': charts,
                'location_history': location_history,
                'favorite_locations': favorite_locations})
    else:
        # Show empty dashboard
        return TemplateResponse(
            request,
            'weather_app/no_location.html', {
                'query': query,
                'location': None,
                'weather': None,
                'air_pollution': None,
                'charts': None,
                'location_history': location_history,
                'favorite_locations': favorite_locations})
