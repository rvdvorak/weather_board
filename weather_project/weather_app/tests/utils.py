from weather_app.models import User, Location
from datetime import datetime
import pickle
import pytz
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from urllib.parse import urlencode


def get_display_modes():
    # Valid display modes
    return [
        '48h_detail',
        '7d_detail']


def get_get_request_and_messages(url, query, user):
    # Setup request
    uri = f'{url}?{urlencode(query)}'
    request = RequestFactory().get(uri)
    request.user = user
    # Add session to request
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    # Add messages to request
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request, messages


def setup_test_user_data():
    credentials = {
        'username': 'test_user',
        'password': '123456'}
    user = User.objects.create_user(**credentials)
    ordinary_location = Location(
        label='Clair, SK, Canada',
        latitude=52.0167,
        longitude=-104.0843,
        is_favorite=False,
        user=user)
    ordinary_location.save()
    favorite_location = Location(
        label='Sydney, NSW, Australia',
        latitude=-33.8686,
        longitude=151.2094,
        is_favorite=True,
        user=user)
    favorite_location.save()
    return {
        'credentials': credentials,
        'user': user,
        'ordinary_location': ordinary_location,
        'favorite_location': favorite_location}


def check_template_context_with_user_data(template_context, user_data):
    # Context data depending on user authentication
    location_history = template_context['location_history']
    assert user_data['favorite_location'] in location_history
    assert user_data['ordinary_location'] in location_history
    favorite_locations = template_context['favorite_locations']
    assert user_data['favorite_location'] in favorite_locations
    assert not user_data['ordinary_location'] in favorite_locations


def check_template_context_with_no_user_data(template_context):
    # Context data depending on user authentication
    assert template_context['location_history'] == None
    assert template_context['favorite_locations'] == None


def check_template_context_with_error_message(template_context, query):
    # Context data depending on query
    query['latitude'] = float(query['latitude'])
    query['longitude'] = float(query['longitude'])
    template_context['query']['latitude'] = float(
        template_context['query']['latitude'])
    template_context['query']['longitude'] = float(
        template_context['query']['longitude'])
    assert template_context['query'] == query
    assert template_context['location'] == None
    assert template_context['weather'] == None
    assert template_context['air_pollution'] == None
    assert template_context['charts'] == None


def check_template_context_with_query(template_context, query):
    # Context data depending on query
    query['latitude'] = float(query['latitude'])
    query['longitude'] = float(query['longitude'])
    template_context['query']['latitude'] = float(
        template_context['query']['latitude'])
    template_context['query']['longitude'] = float(
        template_context['query']['longitude'])
    assert template_context['query'] == query
    location = template_context['location']
    assert location.label == query['label']
    assert location.latitude == query['latitude']
    assert location.longitude == query['longitude']
    weather = template_context['weather']
    assert weather['lat'] == query['latitude']
    assert weather['lon'] == query['longitude']
    assert {*weather['current'].keys()}.issuperset({
        'dt', 'temp', 'feels_like', 'pressure', 'humidity', 'dew_point',
        'clouds', 'uvi', 'visibility', 'wind_speed', 'wind_deg', 'weather'})
    air_pollution = template_context['air_pollution']
    assert air_pollution['coord']['lat'] == query['latitude']
    assert air_pollution['coord']['lon'] == query['longitude']
    charts = template_context['charts']
    assert charts.keys() == {
        'minutely', 'hourly', 'daily', 'air_pollution'}


def check_template_context_with_no_query(template_context):
    # Query in template context is set to default
    assert template_context['query'] == {
        'display_mode': '48h_detail',
        'label': '',
        'latitude': '',
        'longitude': ''}
    # Context data depending on query
    assert template_context['location'] == None
    assert template_context['weather'] == None
    assert template_context['air_pollution'] == None
    assert template_context['charts'] == None


def get_test_query():
    return {
        'display_mode': '7d_detail',
        'label': 'San Matías, SC, Bolivia',
        'latitude': '-16.3667',
        'longitude': '-58.4'}


def sample_location_params_1():
    return {
        'label': 'San Matías, SC, Bolivia',
        'latitude': -16.3667,
        'longitude': -58.4}


def sample_location_params_2():
    return {
        'label': 'Clair, SK, Canada',
        'latitude': 52.0167,
        'longitude': -104.0843}


def sample_location_params_3():
    return {
        'label': 'Sydney, NSW, Australia',
        'latitude': -33.8686,
        'longitude': 151.2094}


def sample_timezone_1():
    return 'America/La_Paz'


def sample_location_instance_1():
    location_params = sample_location_params_1()
    return Location(
        latitude=float(location_params['latitude']),
        longitude=float(location_params['longitude']),
        label=location_params['label'])


# def sample_location_instance_2():
#     location_params = sample_location_params_2()
#     return Location(
#         latitude=float(location_params['latitude']),
#         longitude=float(location_params['longitude']),
#         label=location_params['label'])


# def sample_location_instance_3():
#     location_params = sample_location_params_3()
#     return Location(
#         latitude=float(location_params['latitude']),
#         longitude=float(location_params['longitude']),
#         label=location_params['label'])


def sample_credentials():
    return {
        'username': 'roman',
        'password': '123456'}


def sample_user():
    return User(**sample_credentials())


def required_current_weather_keys():
    # Those keys must be always contained in "current" weather data
    return {
        'dt', 'temp', 'feels_like', 'pressure', 'humidity', 'dew_point',
        'clouds', 'uvi', 'visibility', 'wind_speed', 'wind_deg', 'weather'}


def sample_weather():
    with open('weather_app/tests/sample_data/weather.pkl', 'rb') as file:
        return pickle.load(file)


def sample_air_pollution():
    with open('weather_app/tests/sample_data/air_pollution.pkl', 'rb') as file:
        return pickle.load(file)


def sample_charts():
    with open('weather_app/tests/sample_data/charts.pkl', 'rb') as file:
        return pickle.load(file)


# def sample_location_history():
#     with open('weather_app/tests/sample_data/location_history.pkl', 'rb') as file:
#         return pickle.load(file)


# def sample_favorite_locations():
#     with open('weather_app/tests/sample_data/favorite_locations.pkl', 'rb') as file:
#         pickle.load(file)
