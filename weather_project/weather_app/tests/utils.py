from weather_app.models import User, Location
from datetime import datetime
import pickle
import pytz


def get_sample_location_params():
    return {
        'latitude': '-16.3667',
        'longitude': '-58.4',
        'label': 'San Matías, SC, Bolivia'}


def get_sample_timezone():
    return pytz.timezone('America/La_Paz')


def get_sample_location_instance():
    location_params = get_sample_location_params()
    return Location(
        latitude=float(location_params['latitude']),
        longitude=float(location_params['longitude']),
        label=location_params['label'])


def get_sample_credentials():
    return {
        'username': 'roman',
        'password': '123456'}


def get_sample_user():
    return User(**get_sample_credentials())


def get_sample_weather():
    with open('weather_app/tests/sample_data/weather.pkl', 'rb') as file:
        return pickle.load(file)


def get_sample_air_pollution():
    with open('weather_app/tests/sample_data/air_pollution.pkl', 'rb') as file:
        return pickle.load(file)


def get_sample_charts():
    with open('weather_app/tests/sample_data/charts.pkl', 'rb') as file:
        return pickle.load(file)


def get_sample_location_history():
    with open('weather_app/tests/sample_data/location_history.pkl', 'rb') as file:
        return pickle.load(file)


def get_sample_favorite_locations():
    with open('weather_app/tests/sample_data/favorite_locations.pkl', 'rb') as file:
        pickle.load(file)
