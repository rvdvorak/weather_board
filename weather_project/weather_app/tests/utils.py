from weather_app.models import User, Location
from datetime import datetime
import pickle
import pytz


def sample_location_params_1():
    return {
        'label': 'San Matías, SC, Bolivia',
        'latitude': '-16.3667',
        'longitude': '-58.4'}


def sample_location_params_2():
    return {
        'label': 'Clair, SK, Canada',
        'latitude': '52.0167',
        'longitude': '-104.0843'}


def sample_location_params_3():
    return {
        'label': 'Sydney, NSW, Australia',
        'latitude': '-33.8686',
        'longitude': '151.2094'}


def sample_timezone_1():
    return pytz.timezone('America/La_Paz')


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
