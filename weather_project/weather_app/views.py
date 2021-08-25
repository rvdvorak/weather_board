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
                'location': None,
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
                'location': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect location data',
                    'description': 'Location data type error.',
                }
            }
        if not (-90 <= latitude <= 90):
            return {
                'location': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect coordinates',
                    'description': 'Latitude out of range.',
                }
            }
        if not (-180 <= longitude <= 180):
            return {
                'location': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect coordinates',
                    'description': 'Longitude out of range.',
                }
            }
        if label == '':
            return {
                'location': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incomplete location data',
                    'description': 'Missing location label.',
                }
            }
        return {
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'label': label,
            },
            'message': {
                'style': 'success',
                'headline': 'Location OK',
                'description': 'Location data is correct.',
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
                'weather': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Weather API error',
                    'description': f'Weather server status: {response.status_code}',
                }
            }
        weather = response.json()
        return {
            'weather': weather,
            'message': {
                'style': 'success',
                'headline': 'Weather API response OK',
                'description': 'Weather data received successfully.',
            }
        }

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

    if not location['location']:
        return render(request, 'weather_app/pages/message.html', {'message': location['message']})

    weather = get_weather(location['location'])

    if not weather['weather']:
        return render(request, 'weather_app/pages/message.html', {'message': weather['message']})

    weather['weather'] = convert_timestamps_to_datetime(weather['weather'])

    chart_data = get_chart_data(weather['weather'])

    return render(
        request,
        'weather_app/pages/weather_dashboard.html',
        {
            'location': location['location'],
            'weather': weather['weather'],
            'chart_data': chart_data,
        }
    )


def locations(request):
    search_text = str(request.GET.get('search_text'))

    if not search_text:
        message = {
            'style': 'lightblue',
            'headline': 'Hint',
            'description': 'First enter the name of the location you want to search.',
        }
        return render(request, 'weather_app/pages/locations.html', {'message': message})

    location_API_request = 'https://api.openrouteservice.org/geocode/search?api_key=5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71&size=50&text=' + search_text
    location_API_response = requests.get(location_API_request)

    if not location_API_response.status_code == 200:
        message = {
            'style': 'danger',
            'headline': 'Search location error',
            'description': f'Search request failed. Please try again later. (Location server status: {location_API_response.status_code})',
        }
        return render(request, 'weather_app/pages/locations.html', {'message': message})

    found_locations = location_API_response.json()['features']

    if not found_locations:
        message = {
            'style': 'lightblue',
            'headline': 'No location found',
            'description': 'You probably entered the location incorrectly. Please try again.',
        }
        return render(request, 'weather_app/pages/locations.html', {'message': message})

    return render(request, 'weather_app/pages/locations.html', {'found_locations': found_locations})
