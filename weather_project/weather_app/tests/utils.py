from weather_app.models import User, Location
from datetime import datetime
import pickle
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


def get_test_user_credentials():
    return {
        'username': 'test_user',
        'password': '12345678'}


def setup_test_user_data():
    # Create user account and location data
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
        'username': credentials['username'],
        'password': credentials['password'],
        'user': user,
        'ordinary_location': ordinary_location,
        'favorite_location': favorite_location,
        'ordinary_location_params': ordinary_location_params,
        'favorite_location_params': favorite_location_params}


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


def check_query_is_preserved(context, query):
    # Subset of query params which must be preserved
    # in template context across all pages
    expected_query = get_empty_location_query()
    expected_query.update(query)
    assert context['query'] == expected_query
    

def check_user_data_with_login(context, user_data):
    # User location data available after authentication
    location_history = context['location_history']
    assert user_data['favorite_location'] in location_history
    assert user_data['ordinary_location'] in location_history
    favorite_locations = context['favorite_locations']
    assert user_data['favorite_location'] in favorite_locations
    assert not user_data['ordinary_location'] in favorite_locations


def check_user_data_with_no_login(context):
    # User location data available after authentication
    assert context['location_history'] == None
    assert context['favorite_locations'] == None


def check_weather_data(context, query):
    # Weather data depending on location query
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


def get_sample_weather():
    with open('weather_app/tests/sample_data/weather.pkl', 'rb') as file:
        return pickle.load(file)


def get_sample_air_pollution():
    with open('weather_app/tests/sample_data/air_pollution.pkl', 'rb') as file:
        return pickle.load(file)


def get_sample_charts():
    with open('weather_app/tests/sample_data/charts.pkl', 'rb') as file:
        return pickle.load(file)


# def get_sample_location_history():
#     with open('weather_app/tests/sample_data/location_history.pkl', 'rb') as file:
#         return pickle.load(file)


# def get_sample_favorite_locations():
#     with open('weather_app/tests/sample_data/favorite_locations.pkl', 'rb') as file:
#         pickle.load(file)
