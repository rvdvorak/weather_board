from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from datetime import datetime
from weather_app.models import Location
import requests
from requests.exceptions import Timeout
import json
import pprint
import pytz
import random

# TODO Sunrise/Sunset: http://127.0.0.1:8000/?latitude=81.475139&longitude=-161.169992&label=Arctic+Ocean

def dashboard(request):

    def get_location(request):
        try:
            latitude = request.GET.get('latitude')
            longitude = request.GET.get('longitude')
            label = request.GET.get('label')
            if latitude and longitude and label:
                location = Location(
                    latitude=latitude,
                    longitude=longitude,
                    label=label)
                location.clean_fields(exclude=['user'])
                if request.user.is_authenticated:
                    match = Location.objects.filter(
                        user=request.user,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        label=location.label)
                    if len(match) != 0:  # Location is already saved
                        return match[0]
                    else:  # Location is not saved yet
                        return location
                else:
                    return location
            else:
                messages.info(
                    request, {
                        'header': 'Select location',
                        'description': 'Search location to get started.',
                        'icon': 'bi bi-geo-alt-fill',
                        'show_search_form': True})
                return None
        except ValidationError as err:
            messages.warning(
                request, {
                    'header': 'Incorrect location',
                    'description': 'Try to search the location by its name.',
                    'icon': 'bi bi-geo-alt-fill',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_location(request)',
                        f'Exception: {pprint.pformat(err)}']})
            return None
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Processing location data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_location(request)',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def get_location_history(request):
        try:
            location_history = Location.objects.filter(
                user=request.user).order_by('-date_last_showed')
            return location_history
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Processing location history failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_location_history(request)',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def get_favorite_locations(request):
        try:
            favorite_locations = Location.objects.filter(
                user=request.user,
                is_favorite=True).order_by('-date_last_showed')
            return favorite_locations
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Processing favorite locations failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_favorite_locations(request)',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def get_weather(location):
        # API docs: https://openweathermap.org/api/one-call-api
        try:
            url = 'https://api.openweathermap.org/data/2.5/onecall'
            params = {
                'lat': location.latitude,
                'lon': location.longitude,
                'units': 'metric',
                'appid': '6fe37effcfa866ecec5fd235699a402d'}
            response = requests.get(url, params=params, timeout=5)
            if not response.status_code == 200:
                messages.error(
                    request, {
                        'header': 'Weather service error',
                        'description': 'Request for weather data failed.',
                        'icon': 'fas fa-times-circle',
                        'admin_details': [
                            'Method: get_weather(location)',
                            f'API endpoint: {url}',
                            f'Parameters: {pprint.pformat(params)}',
                            f'HTTP status: {response.status_code}']})
                return None
            weather = response.json()
            return weather
        except Timeout as err:
            messages.warning(
                request, {
                    'header': 'Weather service time out',
                    'description': 'Please try it again later...',
                    'icon': 'fas fa-hourglass-end',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_weather(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {err}']})
            return None
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Processing weather data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_weather(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def get_air_pollution(location):
        # API docs: https://openweathermap.org/api/air-pollution
        try:
            url = 'http://api.openweathermap.org/data/2.5/air_pollution/forecast'
            params = {
                'lat': location.latitude,
                'lon': location.longitude,
                'appid': '6fe37effcfa866ecec5fd235699a402d'}
            response = requests.get(url, params=params, timeout=5)
            if not response.status_code == 200:
                messages.error(
                    request, {
                        'header': 'Air pollution service error',
                        'description': 'Request for data failed.',
                        'icon': 'fas fa-times-circle',
                        'admin_details': [
                            'Method: get_air_pollution(location)',
                            f'API endpoint: {url}',
                            f'Parameters: {pprint.pformat(params)}',
                            f'HTTP status: {response.status_code}']})
                return None
            air_pollution = response.json()['list']
            return air_pollution
        except Timeout as err:
            messages.warning(
                request, {
                    'header': 'Air pollution service time out',
                    'description': 'Please try it again later...',
                    'icon': 'fas fa-hourglass-end',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_air_pollution(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {err}']})
            return None
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Processing air pollution data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_air_pollution(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def convert_timestamps_to_datetimes(weather):
        # TODO Refactor
        try:
            timezone = pytz.timezone(weather['timezone'])
            weather['current']['dt'] = datetime.fromtimestamp(
                weather['current']['dt'], timezone)
            if 'sunrise' in weather['current']:
                weather['current']['sunrise'] = datetime.fromtimestamp(
                    weather['current']['sunrise'], timezone)
            if 'sunset' in weather['current']:
                weather['current']['sunset'] = datetime.fromtimestamp(
                    weather['current']['sunset'], timezone)
            if 'minutely' in weather:
                for minute in range(len(weather['minutely'])):
                    weather['minutely'][minute]['dt'] = datetime.fromtimestamp(
                        weather['minutely'][minute]['dt'], timezone)
            for hour in range(len(weather['hourly'])):
                weather['hourly'][hour]['dt'] = datetime.fromtimestamp(
                    weather['hourly'][hour]['dt'], timezone)
            for day in range(len(weather['daily'])):
                weather['daily'][day]['dt'] = datetime.fromtimestamp(
                    weather['daily'][day]['dt'], timezone)
                weather['daily'][day]['sunrise'] = datetime.fromtimestamp(
                    weather['daily'][day]['sunrise'], timezone)
                weather['daily'][day]['sunset'] = datetime.fromtimestamp(
                    weather['daily'][day]['sunset'], timezone)
            if 'alerts' in weather:
                for alert in range(len(weather['alerts'])):
                    weather['alerts'][alert]['start'] = datetime.fromtimestamp(
                        weather['alerts'][alert]['start'], timezone)
                    weather['alerts'][alert]['end'] = datetime.fromtimestamp(
                        weather['alerts'][alert]['end'], timezone)
            for hour in range(len(weather['air_pollution'])):
                weather['air_pollution'][hour]['dt'] = datetime.fromtimestamp(
                    weather['air_pollution'][hour]['dt'], timezone)
            return weather
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Date/time processing failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: convert_timestamps_to_datetimes(weather)',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def get_charts(weather):
        try:
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
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Processing chart data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_charts(weather)',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def save_location(location):
        try:
            match = Location.objects.filter(
                user=request.user,
                longitude=location.longitude,
                latitude=location.latitude,
                label=location.label)
            if len(match) == 0:
                location.user = request.user
                location.save()
            else:
                match[0].is_favorite = location.is_favorite
                match[0].save()
            return
        except Exception as err:
            messages.error(
                request, {
                    'header': 'Internal error',
                    'description': 'Location saving failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: save_location(location)',
                        f'Exception: {pprint.pformat(err)}']})
            return

    try:
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        label = request.GET.get('label')
        if latitude and longitude and label:
            location = get_location(request)
            if location:
                weather = get_weather(location)
                air_pollution = get_air_pollution(location)
                if weather and air_pollution:
                    weather['air_pollution'] = air_pollution
                    weather = convert_timestamps_to_datetimes(
                        weather)
                    weather['charts'] = get_charts(weather)
                    if request.user.is_authenticated:
                        save_location(location)
        else:
            location = None
            weather = None
        if request.user.is_authenticated:
            location_history = get_location_history(request)
            favorite_locations = get_favorite_locations(request)
        else:
            location_history = None
            favorite_locations = None
        return render(
            request,
            'weather_app/dashboard.html', {
                'location': location,
                'weather': weather,
                'location_history': location_history,
                'favorite_locations': favorite_locations})
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'Dashboard processing failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: dashboard(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')
