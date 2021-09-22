from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from weather_app.models import Location
import requests
import json
import pprint
import pytz


def dashboard(request):
    # TODO Exceptions
    def save_location(location, request):
        new_location = Location(
            label=location['label'],
            latitude=location['latitude'],
            longitude=location['longitude'],
            favourite=False,
            date_last_showed=datetime.now(),
            user=request.user)
        new_location.save()
        return

    def get_location(request):
        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
            label = str(request.GET.get('label'))
            if not (-90 <= latitude <= 90) and (-180 <= longitude <= 180):
                raise Exception('Coordinates out of range.')
            if label == '':
                raise Exception('Missing location label.')
            return {
                'data': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'label': label}}
        except Exception as err:
            return {
                'message': {
                    'style': 'lightblue',
                    'headline': 'Select location',
                    'description': 'Search location to get started.',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_location(request)',
                        f'Exception: {pprint.pformat(err)}']}}

    def get_weather(location):
        # API docs: https://openweathermap.org/api/one-call-api
        try:
            url = 'https://api.openweathermap.org/data/2.5/onecall'
            params = {
                'lat': location['latitude'],
                'lon': location['longitude'],
                'units': 'metric',
                'appid': '6fe37effcfa866ecec5fd235699a402d'}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Data processing failed.',
                    'admin_details': [
                        'Method: get_weather(location)',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Weather service is not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_weather(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            if not response.status_code == 200:
                raise Exception('HTTP response failed')
            weather = response.json()
            return {'data': weather}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Weather service error',
                    'description': 'Request for data failed.',
                    'admin_details': [
                        'Method: get_weather(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'HTTP status: {response.status_code}',
                        f'Exception: {pprint.pformat(err)}']}}

    def get_air_pollution(location):
        # API docs: https://openweathermap.org/api/air-pollution
        try:
            url = 'http://api.openweathermap.org/data/2.5/air_pollution/forecast'
            params = {
                'lat': location['latitude'],
                'lon': location['longitude'],
                'appid': '6fe37effcfa866ecec5fd235699a402d'}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Data processing failed.',
                    'admin_details': [
                        'Method: get_air_pollution(location)',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Air pollution service is not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_air_pollution(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            if not response.status_code == 200:
                raise Exception('HTTP response failed')
            air_pollution = response.json()['list']
            return {'data': air_pollution}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Air pollution service error',
                    'description': 'Request for data failed.',
                    'admin_details': [
                        'Method: get_air_pollution(location)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'HTTP status: {response.status_code}',
                        f'Exception: {pprint.pformat(err)}']}}

    def convert_UTC_timestamps_to_local_datetimes(weather):
        # REFACTOR convert_UTC_timestamps_to_local_datetimes(weather)
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
            return {'data': weather}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Data processing failed.',
                    'admin_details': [
                        'Method: convert_UTC_timestamps_to_local_datetimes(weather)',
                        f'Exception: {pprint.pformat(err)}']}}

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
            return {'data': charts}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Data processing failed.',
                    'admin_details': [
                        'Method: get_charts(weather)',
                        f'Exception: {pprint.pformat(err)}']}}

    try:
        location = get_location(request)
        if not 'data' in location:
            return render(request, 'weather_app/message.html', {'message': location['message']})
        weather = get_weather(location['data'])
        if not 'data' in weather:
            return render(request, 'weather_app/message.html', {'message': weather['message']})
        air_pollution = get_air_pollution(location['data'])
        if not 'data' in air_pollution:
            return render(request, 'weather_app/message.html', {'message': air_pollution['message']})
        weather['data']['air_pollution'] = air_pollution['data']
        weather = convert_UTC_timestamps_to_local_datetimes(weather['data'])
        if not 'data' in weather:
            return render(request, 'weather_app/message.html', {'message': weather['message']})
        charts = get_charts(weather['data'])
        if not 'data' in charts:
            return render(request, 'weather_app/message.html', {'message': charts['message']})
        weather['data']['charts'] = charts['data']
        if request.user.is_authenticated:
            save_location(location['data'], request)
        return render(request, 'weather_app/dashboard.html', {
            'location': location['data'],
            'weather': weather['data']})
    except Exception as err:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'danger',
                'headline': 'Internal error',
                'description': 'Data processing failed.',
                'admin_details': [
                    'Method: dashboard(request)',
                    f'Exception: {pprint.pformat(err)}']}})
