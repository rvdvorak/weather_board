from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import requests
import json
import pprint
import pytz


def dashboard(request):
    def get_location(request):
        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
            label = str(request.GET.get('label'))
        except Exception as err:
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Missing or incorrect location data',
                    'description': 'Try to search the location.',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_location(request)',
                        f'Exception: {pprint.pformat(err)}']}}
        if not (-90 <= latitude <= 90) and (-180 <= longitude <= 180):
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Incorrect location',
                    'description': 'Coordinates out of range. Try to search the location.',
                    'show_search_form': True}}
        if label == '':
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Missing location label',
                    'description': 'Try to search the location.',
                    'show_search_form': True}}
        return {
            'data': {
                'latitude': latitude,
                'longitude': longitude,
                'label': label}}

    def get_weather(location):
        # API docs: https://openweathermap.org/api/one-call-api
        url = 'https://api.openweathermap.org/data/2.5/onecall'
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'units': 'metric',
            'appid': '6fe37effcfa866ecec5fd235699a402d'}
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
                        f'Exception: {pprint.pformat(err)}']}}
        if not response.status_code == 200:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Weather service error',
                    'description': 'Request for data failed.',
                    'admin_details': [
                        'Method: get_weather(location)',
                        f'API endpoint: {url}',
                        f'HTTP status: {response.status_code}']}}
        weather = response.json()
        return {'data': weather}

    def get_air_pollution(location):
        # API docs: https://openweathermap.org/api/air-pollution
        url = 'http://api.openweathermap.org/data/2.5/air_pollution/forecast'
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'appid': '6fe37effcfa866ecec5fd235699a402d'}
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
                        f'Exception: {pprint.pformat(err)}']}}
        if not response.status_code == 200:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Air pollution service error',
                    'description': 'Request for data failed.',
                    'admin_details': [
                        'Method: get_air_pollution(location)',
                        f'API endpoint: {url}',
                        f'HTTP status: {response.status_code}']}}
        #TODO Add try/except: Internal error - Unexpected data structure
        air_pollution = response.json()['list']
        return {'data': air_pollution}

    def convert_UTC_timestamps_to_local_datetimes(weather):
        # REFACTOR Convert UTC timestamps to selected location's datetime
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
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Data processing failed.',
                    'admin_details': [
                        'Method: convert_UTC_timestamps_to_local_datetimes(weather)',
                        f'Exception: {pprint.pformat(err)}']}}
        return {'data': weather}

    def add_chart_data(weather):
    #TODO Transform to "get_chart_data(weather)"
        try:
            if 'minutely' in weather:
                minutely_chart = {
                    'time': [],
                    'volume': [],
                }
                for minute in weather['minutely']:
                    minutely_chart['time'].append(minute['dt'].strftime("%H:%M"))
                    minutely_chart['volume'].append(
                        round(minute['precipitation'], 1))
                weather['minutely_chart'] = minutely_chart
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Data processing failed.',
                    'admin_details': [
                        'Method: add_chart_data(weather)',
                        f'Exception: {pprint.pformat(err)}']}}
        return {'data': weather}

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

    weather = add_chart_data(weather['data'])
    if not 'data' in weather:
        return render(request, 'weather_app/message.html', {'message': weather['message']})

    return render(request, 'weather_app/dashboard.html', {
        'location': location['data'],
        'weather': weather['data']})