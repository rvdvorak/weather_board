from weather_app.models import User, Location
from datetime import datetime
import pickle
import pytz
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from urllib.parse import urlencode


def get_valid_display_modes():
    # Valid display modes
    return [
        '48h_detail',
        '7d_detail']


def get_empty_location_query():
    return {
        'display_mode': get_valid_display_modes()[0],
        'search_text': '',
        'label': '',
        'latitude': '',
        'longitude': ''}


def get_test_location_query():
    return {
        'display_mode': get_valid_display_modes()[1],
        'search_text': '',
        'label': 'San Matías, SC, Bolivia',
        'latitude': '-16.3667',
        'longitude': '-58.4'}


def setup_get_request_with_messages(url, query, user):
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


def get_test_user_credentials():
    return {
        'username': 'test_user',
        'password': '12345678'}


def setup_test_user_data():
    credentials = get_test_user_credentials()
    user = User.objects.create_user(**credentials)
    ordinary_location_params = {
        'label': 'Clair, SK, Canada',
        'latitude': '52.0167',
        'longitude': '-104.0843'}
    ordinary_location = Location(
        **ordinary_location_params,
        is_favorite=False,
        user=user)
    ordinary_location.save()
    favorite_location_params = {
        'label': 'Sydney, NSW, Australia',
        'latitude': '-33.8686',
        'longitude': '151.2094'}
    favorite_location = Location(
        **favorite_location_params,
        is_favorite=True,
        user=user)
    favorite_location.save()
    return {
        'credentials': credentials,
        'user': user,
        'ordinary_location': ordinary_location,
        'favorite_location': favorite_location,
        'ordinary_location_params': ordinary_location_params,
        'favorite_location_params': favorite_location_params}


def check_context_with_user_data(context, user_data):
    # Context data depending on user authentication
    location_history = context['location_history']
    assert user_data['favorite_location'] in location_history
    assert user_data['ordinary_location'] in location_history
    favorite_locations = context['favorite_locations']
    assert user_data['favorite_location'] in favorite_locations
    assert not user_data['ordinary_location'] in favorite_locations


def check_context_with_no_user_data(context):
    # Context data depending on user authentication
    assert context['location_history'] == None
    assert context['favorite_locations'] == None


def check_context_with_message(context, query):
    # Context data depending on query
    expected_query = get_empty_location_query()
    expected_query.update(query)
    assert context['query'] == expected_query
    assert context['location'] == None
    assert context['weather'] == None
    assert context['air_pollution'] == None
    assert context['charts'] == None


def check_context_with_location_query(context, query):
    # Context data depending on query
    assert context['query'] == query
    location = context['location']
    assert location.label == query['label']
    assert location.latitude == float(query['latitude'])
    assert location.longitude == float(query['longitude'])
    weather = context['weather']
    assert weather['lat'] == float(query['latitude'])
    assert weather['lon'] == float(query['longitude'])
    assert {*weather['current'].keys()}.issuperset({
        'dt', 'temp', 'feels_like', 'pressure', 'humidity', 'dew_point',
        'clouds', 'uvi', 'visibility', 'wind_speed', 'wind_deg', 'weather'})
    air_pollution = context['air_pollution']
    assert air_pollution['coord']['lat'] == float(query['latitude'])
    assert air_pollution['coord']['lon'] == float(query['longitude'])
    charts = context['charts']
    assert charts.keys() == {
        'minutely', 'hourly', 'daily', 'air_pollution'}


def check_context_with_no_query(context):
    # Context data depending on query
    assert context['query'] == get_empty_location_query()
    assert context['location'] == None
    assert context['weather'] == None
    assert context['air_pollution'] == None
    assert context['charts'] == None


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


def sample_user():
    return User(**get_test_user_credentials())


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
