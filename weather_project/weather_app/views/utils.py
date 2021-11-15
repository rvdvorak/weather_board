from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from datetime import datetime
from weather_app.models import Location
from django.contrib.auth.models import User
import requests
import json
import pytz
import random


def redirect_to_dashboard(location_params):
    base_url = reverse('dashboard')
    params = urlencode(location_params)
    uri = f'{base_url}?{params}'
    return redirect(uri)


def render_dashboard(request, location=None, weather=None, air_pollution=None, charts=None):
    return render(
        request,
        'weather_app/dashboard.html', {
            'location': location,
            'weather': weather,
            'air_pollution': air_pollution,
            'charts': charts,
            'location_history': get_location_history(request.user),
            'favorite_locations': get_favorite_locations(request.user)})


def render_user_profile(request, error_message=None, success_message=None):
    return render(
        request,
        'weather_app/user_profile.html', {
            'success_message': success_message,
            'error_message': error_message,
            'location_params': get_location_params(request),
            'location_history': get_location_history(request.user),
            'favorite_locations': get_favorite_locations(request.user)})


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


def get_random_location_params(ORS_key, timeout=5):
    # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get
    url = 'https://api.openrouteservice.org/geocode/reverse'
    latitude = round(
        random.random() * 180 - 90,
        6)
    longitude = round(
        random.random() * 360 - 180,
        6)
    params = {
        'api_key': ORS_key,
        'point.lat': latitude,
        'point.lon': longitude,
        'size': 1}
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return {
        'latitude': latitude,
        'longitude': longitude,
        'label': response.json()['features'][0]['properties']['label']}


def get_search_results(search_query, ORS_key, timeout=5, max_count=20):
    # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/search/get
    url = 'https://api.openrouteservice.org/geocode/search'
    params = {
        'api_key': ORS_key,
        'size': max_count,
        'text': search_query}
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()['features']


def get_location_instance(location_params, user):
    if location_params:
        location_instance = Location(
            latitude=location_params['latitude'],
            longitude=location_params['longitude'],
            label=location_params['label'])
        location_instance.clean_fields(exclude=['user'])
        if user.is_authenticated:
            location_instance.user = user
            match = Location.objects.filter(
                user=user,
                latitude=location_instance.latitude,
                longitude=location_instance.longitude,
                label=location_instance.label)
            if len(match) != 0:
                # Location is already saved in DB
                location_instance = match[0]
        return location_instance
    else:
        return None


def get_location_history(user):
    if user.is_authenticated:
        return Location.objects.filter(
            user=user).order_by('-date_last_showed')
    else:
        return None


def get_favorite_locations(user):
    if user.is_authenticated:
        return Location.objects.filter(
            user=user,
            is_favorite=True).order_by('-date_last_showed')
    else:
        return None


def convert_timestamps_to_datetimes(data, keys_to_convert, timezone):
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys_to_convert:
                data[key] = datetime.fromtimestamp(value, timezone)
            elif isinstance(value, dict) or isinstance(value, list):
                data[key] = convert_timestamps_to_datetimes(
                    value, keys_to_convert, timezone)
    elif isinstance(data, list):
        for index in range(len(data)):
            data[index] = convert_timestamps_to_datetimes(
                data[index], keys_to_convert, timezone)
    return data


def get_weather(location, OWM_key, timeout=5):
    # API docs: https://openweathermap.org/api/one-call-api
    base_url = 'https://api.openweathermap.org/data/2.5/onecall'
    params = {
        'lat': location.latitude,
        'lon': location.longitude,
        'units': 'metric',
        'appid': OWM_key}
    response = requests.get(base_url, params=params, timeout=timeout)
    response.raise_for_status()
    weather = response.json()
    timezone = pytz.timezone(weather['timezone'])
    keys_to_convert = ['dt', 'sunrise', 'sunset', 'start', 'end']
    weather = convert_timestamps_to_datetimes(
        weather, keys_to_convert, timezone)
    return weather


def get_air_pollution(location, timezone, OWM_key, timeout=5):
    # API docs: https://openweathermap.org/api/air-pollution
    url = 'http://api.openweathermap.org/data/2.5/air_pollution/forecast'
    params = {
        'lat': location.latitude,
        'lon': location.longitude,
        'appid': OWM_key}
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    air_pollution = response.json()['list']
    air_pollution = convert_timestamps_to_datetimes(
        air_pollution, ['dt'], timezone)
    return air_pollution


def get_charts(weather):
    charts = {
        'minutely': {
            'timeline': [],
            'precipitation': []},
        'hourly': {
            'timeline': [],
            'pop': [],
            'temp': [],
            'feels_like': [],
            'dew_point': [],
            'clouds': [],
            'humidity': [],
            'pressure': [],
            'wind_speed': [],
            'wind_gust': [],
            'uvi': [],
            'visibility': []},
        'daily': {
            'timeline': []}}
    if 'minutely' in weather:
        for minute in weather['minutely']:
            charts['minutely']['timeline'].append(
                minute['dt'].strftime("%H:%M"))
            charts['minutely']['precipitation'].append(
                round(minute['precipitation'], 2))
    if 'hourly' in weather:
        for hour in weather['hourly']:
            charts['hourly']['timeline'].append(
                hour['dt'].strftime("%a %H:%M"))
            charts['hourly']['pop'].append(
                hour['pop']*100)
            charts['hourly']['temp'].append(
                round(hour['temp'], 1))
            charts['hourly']['feels_like'].append(
                round(hour['feels_like'], 1))
            charts['hourly']['dew_point'].append(
                round(hour['dew_point'], 1))
            charts['hourly']['clouds'].append(
                hour['clouds'])
            charts['hourly']['humidity'].append(
                hour['humidity'])
            charts['hourly']['pressure'].append(
                hour['pressure'])
            charts['hourly']['wind_speed'].append(
                hour['wind_speed'])
            charts['hourly']['wind_gust'].append(
                hour['wind_gust'])
            charts['hourly']['uvi'].append(
                hour['uvi'])
            charts['hourly']['visibility'].append(
                hour['visibility'])
    return charts
