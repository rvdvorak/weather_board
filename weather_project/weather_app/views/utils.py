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
import pickle


def get_credentials(request):
    return {
        'username': request.POST.get('username'),
        'password': request.POST.get('password')}


def get_location_query(request):
    # Return a subset of HTTP request parameters
    # which must be preserved across all pages.
    query = {}
    params = [
        'display_mode',
        'search_text',
        'label',
        'latitude',
        'longitude']
    if request.method == 'GET':
        for key in params:
            query[key] = request.GET.get(key) or ''
    elif request.method == 'POST':
        for key in params:
            query[key] = request.POST.get(key) or ''
    valid_display_modes = [
        '48h_detail',
        '7d_detail']
    if not query['display_mode'] in valid_display_modes:
        query['display_mode'] = valid_display_modes[0]
    return query


def get_location_history(user):
    # Return all location records owned by the user
    if user.is_authenticated:
        location_history = Location.objects.filter(
            user=user).order_by('-date_last_showed')
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/location_history.pkl', 'wb') as file:
        #     pickle.dump(location_history, file)
        return location_history
    return None


def get_favorite_locations(user):
    # Return only favorite location records owned by the user
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


def redirect_to_login(query):
    base_url = reverse('login_user')
    query_string = urlencode(query)
    uri = f'{base_url}?{query_string}'
    return redirect(uri)


def render_dashboard(request, location=None, weather=None, air_pollution=None, charts=None):
    # Handle appropriate rendering of dashboard
    query = get_location_query(request)
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
                'query': query,
                'location': location,
                'weather': weather,
                'air_pollution': air_pollution,
                'charts': charts,
                'location_history': location_history,
                'favorite_locations': favorite_locations})
    else:
        # Show search location page
        return TemplateResponse(
            request,
            'weather_app/search_location.html', {
                'query': query,
                'location': None,
                'weather': None,
                'air_pollution': None,
                'charts': None,
                'location_history': location_history,
                'favorite_locations': favorite_locations,
                'location_search_page': True})
