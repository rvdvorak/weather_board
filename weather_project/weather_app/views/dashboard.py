from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from datetime import datetime
from weather_app.models import Location
import requests
from requests.exceptions import Timeout
import json
import pprint
import pytz


def dashboard(request):
    def get_location(request):
        try:
            location = Location(
                latitude=request.GET.get('latitude'),
                longitude=request.GET.get('longitude'),
                label=request.GET.get('label'))
            location.clean_fields(exclude=['favorite', 'date_last_showed', 'user'])
            return location
        except ValidationError as err:
            messages.info(request, {
                'headline': 'Select location',
                'description': 'Search location to get started.',
                'icon': 'bi bi-geo-alt-fill',
                'show_search_form': True,
                'admin_details': [
                    'Method: get_location(request)',
                    f'Exception: {pprint.pformat(err)}']})
            return None
        except Exception as err:
            messages.error(request, {
                'headline': 'Internal error',
                'description': 'Processing location data failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: get_location(request)',
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
                messages.error(request, {
                    'headline': 'Weather service error',
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
            messages.warning(request, {
                'headline': 'Weather service time out',
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
            messages.error(request, {
                'headline': 'Internal error',
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
                messages.error(request, {
                    'headline': 'Air pollution service error',
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
            messages.warning(request, {
                'headline': 'Air pollution service time out',
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
            messages.error(request, {
                'headline': 'Internal error',
                'description': 'Processing air pollution data failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: get_air_pollution(location)',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'Exception: {pprint.pformat(err)}']})
            return None

    def convert_UTC_timestamps_to_local_datetimes(weather):
        # TODO REFACTOR convert_UTC_timestamps_to_local_datetimes(weather)
        try:
            timezone = pytz.timezone(weather['timezone'])
            utc_offset = weather['timezone_offset']
            weather['current']['dt'] = datetime.fromtimestamp(
                weather['current']['dt'] + utc_offset, timezone)
            weather['current']['sunrise'] = datetime.fromtimestamp(
                weather['current']['sunrise'] + utc_offset, timezone)
            weather['current']['sunset'] = datetime.fromtimestamp(
                weather['current']['sunset'] + utc_offset, timezone)
            if 'minutely' in weather:
                for minute in range(len(weather['minutely'])):
                    weather['minutely'][minute]['dt'] = datetime.fromtimestamp(
                        weather['minutely'][minute]['dt'] + utc_offset, timezone)
            for hour in range(len(weather['hourly'])):
                weather['hourly'][hour]['dt'] = datetime.fromtimestamp(
                    weather['hourly'][hour]['dt'] + utc_offset, timezone)
            for day in range(len(weather['daily'])):
                weather['daily'][day]['dt'] = datetime.fromtimestamp(
                    weather['daily'][day]['dt'] + utc_offset, timezone)
                weather['daily'][day]['sunrise'] = datetime.fromtimestamp(
                    weather['daily'][day]['sunrise'] + utc_offset, timezone)
                weather['daily'][day]['sunset'] = datetime.fromtimestamp(
                    weather['daily'][day]['sunset'] + utc_offset, timezone)
            if 'alerts' in weather:
                for alert in range(len(weather['alerts'])):
                    weather['alerts'][alert]['start'] = datetime.fromtimestamp(
                        weather['alerts'][alert]['start'] + utc_offset, timezone)
                    weather['alerts'][alert]['end'] = datetime.fromtimestamp(
                        weather['alerts'][alert]['end'] + utc_offset, timezone)
            for hour in range(len(weather['air_pollution'])):
                weather['air_pollution'][hour]['dt'] = datetime.fromtimestamp(
                    weather['air_pollution'][hour]['dt'] + utc_offset, timezone)
            return weather
        except Exception as err:
            messages.error(request, {
                'headline': 'Internal error',
                'description': 'Date/time processing failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: convert_UTC_timestamps_to_local_datetimes(weather)',
                    f'Exception: {pprint.pformat(err)}']})
            return None

    def get_charts(weather):
        try:
            charts = {}
            if 'minutely' in weather:
                time = []
                volume = []
                for minute in weather['minutely']:
                    time.append(minute['dt'].strftime("%H:%M"))
                    volume.append(round(minute['precipitation'], 2))
                charts['minutely_precipitation'] = {
                    'time': time,
                    'volume': volume}
            return charts
        except Exception as err:
            messages.error(request, {
                'headline': 'Internal error',
                'description': 'Processing chart data failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: get_charts(weather)',
                    f'Exception: {pprint.pformat(err)}']})
            return None

    def save_location(location):
        match = Location.objects.filter(
            longitude=location.longitude,
            latitude=location.latitude)
        if len(match) == 0:
            location.user = request.user
            location.save()
        else:
            match[0].save()
        return
            
    try:
        location = get_location(request)
        if location == None:
            return render(request, 'weather_app/message.html')
        weather = get_weather(location)
        if weather == None:
            return render(request, 'weather_app/message.html')
        air_pollution = get_air_pollution(location)
        if air_pollution == None:
            return render(request, 'weather_app/message.html')
        weather['air_pollution'] = air_pollution
        weather = convert_UTC_timestamps_to_local_datetimes(weather)
        if weather == None:
            return render(request, 'weather_app/message.html')
        charts = get_charts(weather)
        if charts == None:
            return render(request, 'weather_app/message.html')
        weather['charts'] = charts
        if request.user.is_authenticated:
            save_location(location)
        return render(request, 'weather_app/dashboard.html', {
            'location': location,
            'weather': weather})
    except Exception as err:
        messages.error(request, {
            'headline': 'Internal error',
            'description': 'Processing dashboard data failed.',
            'icon': 'fas fa-times-circle',
            'admin_details': [
                'Method: dashboard(request)',
                f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
