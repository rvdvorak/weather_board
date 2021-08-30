from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import requests
import pprint
import json


def weather_dashboard(request):
    def get_location(request):
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        label = request.GET.get('label')
        if not (latitude and longitude and label):
            return {
                'data': None,
                'message': {
                    'style': 'lightblue',
                    'headline': 'No location selected',
                    'description': 'Search location to get started.',
                }
            }
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            label = str(label)
        except:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect location data',
                    'description': 'Location data type error.',
                }
            }
        if not (-90 <= latitude <= 90):
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect coordinates',
                    'description': 'Latitude out of range.',
                }
            }
        if not (-180 <= longitude <= 180):
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect coordinates',
                    'description': 'Longitude out of range.',
                }
            }
        if label == '':
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incomplete location data',
                    'description': 'Missing location label.',
                }
            }
        return {
            'data': {
                'latitude': latitude,
                'longitude': longitude,
                'label': label,
            }
        }

    def get_weather(location):
        url = 'https://api.openweathermap.org/data/2.5/onecall'
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'units': 'metric',
            'appid': '6fe37effcfa866ecec5fd235699a402d',
        }
        response = requests.get(url, params=params)
        if not response.status_code == 200:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Weather API error',
                    'description': f'Weather server status: {response.status_code}',
                }
            }
        weather = response.json()
        return {
            'data': weather,
        }

    def get_air_pollution(location):
        pass

    def convert_timestamps_to_datetime(weather):
        weather['current']['dt'] = datetime.fromtimestamp(
            weather['current']['dt'])
        weather['current']['sunrise'] = datetime.fromtimestamp(
            weather['current']['sunrise'])
        weather['current']['sunset'] = datetime.fromtimestamp(
            weather['current']['sunset'])
        for minute in range(len(weather['minutely'])):
            weather['minutely'][minute]['dt'] = datetime.fromtimestamp(
                weather['minutely'][minute]['dt'])
        return weather

    def get_chart_data(weather):
        chart_data = {
            'precipitation_forecast_1h': {
                'dt': [],
                'precipitation': [],
            }
        }
        for minute in weather['minutely']:
            chart_data['precipitation_forecast_1h']['dt'].append(
                minute['dt'].strftime("%H:%M"))
            chart_data['precipitation_forecast_1h']['precipitation'].append(
                minute['precipitation'])
        return chart_data

    location = get_location(request)
    if not location['data']:
        return render(request, 'weather_app/pages/message.html', {'message': location['message']})
    weather = get_weather(location['data'])
    if not weather['data']:
        return render(request, 'weather_app/pages/message.html', {'message': weather['message']})
    weather['data'] = convert_timestamps_to_datetime(weather['data'])
    chart_data = get_chart_data(weather['data'])
    return render(request, 'weather_app/pages/weather_dashboard.html',
        {
            'location': location['data'],
            'weather': weather['data'],
            'chart_data': chart_data,
        }
    )


def locations(request):
    def search_locations(request):
        search_text = request.GET.get('search_text')
        if not search_text:
            return {
                'data': None,
                'message': {
                    'style': 'warning',
                    'headline': 'Notice',
                    'description': 'First enter the name of the location you want to search.',
                }
            }
        try:
            search_text = str(search_text)
        except:
            return {
                'data': None,
                'message': {
                    'style': 'warning',
                    'headline': 'Notice',
                    'description': 'First enter the name of the location you want to search.',
                }
            }

        url = 'https://api.openrouteservice.org/geocode/search'
        params = {
            'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
            'size': 20,
            'text': search_text,
        }
        response = requests.get(url, params=params)
        if not response.status_code == 200:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Search location failed',
                    'description': f'Location server status: {response.status_code}',
                }
            }
        found_locations = response.json()['features']
        if not found_locations:
            return {
                'data': None,
                'message' : {
                    'style': 'warning',
                    'headline': 'No location found',
                    'description': 'You probably entered the location incorrectly. Please try again.',
                }
            }
        return {
            'data': found_locations,
        }

    found_locations = search_locations(request)
    if not found_locations['data']:
        return render(request, 'weather_app/pages/message.html', {'message': found_locations['message']})
    return render(request, 'weather_app/pages/locations.html', {'found_locations': found_locations['data']})
