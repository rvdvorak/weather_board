from django.contrib import messages
from requests.exceptions import Timeout, HTTPError
from django.core.exceptions import ValidationError
from datetime import datetime
import pytz
from weather_app.views.utils import get_query, render_dashboard
from weather_app.views.API_keys import OWM_key
from weather_app.models import Location
import requests
import pprint
# Persist sample data for testing
import pickle


# TODO Sunrise/Sunset: http://127.0.0.1:8000/?latitude=81.475139&longitude=-161.169992&label=Arctic+Ocean

def get_weather(location, weather_key, weather_timeout):
    # Weather API docs:
    # https://openweathermap.org/api/one-call-api

    base_url = 'https://api.openweathermap.org/data/2.5/onecall'
    params = {
        'lat': location.latitude,
        'lon': location.longitude,
        'units': 'metric',
        'appid': weather_key}
    response = requests.get(base_url, params=params, timeout=weather_timeout)
    response.raise_for_status()
    weather = response.json()
    timezone = pytz.timezone(weather['timezone'])
    keys_to_convert = ['dt', 'sunrise', 'sunset', 'start', 'end']
    weather = convert_timestamps_to_datetimes(
        weather, keys_to_convert, timezone)
    return weather


def get_air_pollution(location, timezone, air_pltn_key, air_pltn_timeout):
    # Air pollution API docs:
    # https://openweathermap.org/api/air-pollution

    url = 'http://api.openweathermap.org/data/2.5/air_pollution/forecast'
    params = {
        'lat': location.latitude,
        'lon': location.longitude,
        'appid': air_pltn_key}
    response = requests.get(url, params=params, timeout=air_pltn_timeout)
    response.raise_for_status()
    air_pollution = response.json()
    air_pollution = convert_timestamps_to_datetimes(
        air_pollution, ['dt'], timezone)
    return air_pollution


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


def get_charts(weather, air_pollution):
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
            'visibility': [],
            'aqi': []},
        'daily': {
            'timeline': [],
            'min_temp': [],
            'max_temp': [],
            'pop': [],
            'clouds': [],
            'humidity': [],
            'pressure': [],
            'wind_speed': [],
            'wind_gust': [],
            'uvi': []},
        'air_pollution': {
            'timeline': [],
            'aqi': []}}
    if 'minutely' in weather:
        for minute in weather['minutely']:
            charts['minutely']['timeline'].append(
                minute['dt'].strftime("%H:%M"))
            charts['minutely']['precipitation'].append(
                round(minute['precipitation'], 2))
    for hour in weather['hourly']:
        charts['hourly']['timeline'].append(
            hour['dt'].strftime("%a %H:%M"))
        charts['hourly']['temp'].append(
            round(hour['temp'], 1))
        charts['hourly']['feels_like'].append(
            round(hour['feels_like'], 1))
        charts['hourly']['dew_point'].append(
            round(hour['dew_point'], 1))
        charts['hourly']['pop'].append(
            hour['pop']*100)
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
    for day in weather['daily']:
        charts['daily']['timeline'].append(
            day['dt'].strftime('%a %d. %b'))
        charts['daily']['min_temp'].append(
            round(day['temp']['min'], 1))
        charts['daily']['max_temp'].append(
            round(day['temp']['max'], 1))
        charts['daily']['pop'].append(
            day['pop']*100)
        charts['daily']['clouds'].append(
            day['clouds'])
        charts['daily']['humidity'].append(
            day['humidity'])
        charts['daily']['pressure'].append(
            day['pressure'])
        charts['daily']['wind_speed'].append(
            day['wind_speed'])
        charts['daily']['wind_gust'].append(
            day['wind_gust'])
        charts['daily']['uvi'].append(
            day['uvi'])
    for hour in air_pollution['list']:
        charts['air_pollution']['timeline'].append(
            hour['dt'].strftime("%a %d. %H:%M"))
        charts['air_pollution']['aqi'].append(
            hour['main']['aqi'])
    return charts


def get_location_instance(query, user):
    if query['label'] and query['latitude'] and query['longitude']:
        location_instance = Location(
            label=query['label'],
            latitude=query['latitude'],
            longitude=query['longitude'])
        location_instance.clean_fields(exclude=['user'])
        if user.is_authenticated:
            # Check if the location is new
            location_instance.user = user
            match = Location.objects.filter(
                user=user,
                latitude=location_instance.latitude,
                longitude=location_instance.longitude,
                label=location_instance.label)
            if len(match) != 0:
                # Location is already saved in DB
                return match[0]
        return location_instance
    # Missing or incomplete location query
    return None


def dashboard(request, weather_key=OWM_key, air_pltn_key=OWM_key, weather_timeout=5, air_pltn_timeout=5):
    user = request.user
    query = get_query(request)
    try:
        location = get_location_instance(query, user)
    except ValidationError as err:
        messages.error(
            request, {
                'header': 'Incorrect location parameters',
                'description': 'Try to search the location by its name.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    if not location:
        return render_dashboard(request)
    try:
        weather = get_weather(location, weather_key, weather_timeout)
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/weather.pkl', 'wb') as file:
        #     pickle.dump(weather, file)
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Weather service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Weather service error',
                'description': 'Communication with weather server failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    timezone = pytz.timezone(weather['timezone'])
    try:
        air_pollution = get_air_pollution(
            location, timezone, air_pltn_key, air_pltn_timeout)
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/air_pollution.pkl', 'wb') as file:
        #     pickle.dump(air_pollution, file)
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Air pollution service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Air pollution service error',
                'description': 'Communication with air pollution server failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    charts = get_charts(weather, air_pollution)
    # Persist sample data for testing
    # with open('weather_app/tests/sample_data/charts.pkl', 'wb') as file:
    #     pickle.dump(charts, file)
    if user.is_authenticated:
        location.save()
    return render_dashboard(
        request,
        location=location,
        weather=weather,
        air_pollution=air_pollution,
        charts=charts)
