from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import requests
import pprint
import json


def weather_dashboard(request):
    def get_location(request):
        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
            label = str(request.GET.get('label'))
        except:
            print('location type error')
            return False
        if not (-90 <= latitude <= 90):
            print('location latitude out of range')
            return False
        if not (-180 <= longitude <= 180):
            print('location longitude out of range')
            return False
        if label == '':
            print('location missing label')
            return False
        location = {
            'latitude': latitude,
            'longitude': longitude,
            'label': label,
        }
        print('location:')
        pprint.pprint(location)
        return location

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
            print('Weather server status:', response.status_code)
            return False
        weather = response.json()
        return weather

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

    if not location:
        message = {
            'style': 'lightblue',
            'headline': 'Hint',
            'description': 'Search location to get started.'
        }
        return render(request, 'weather_app/pages/weather_dashboard.html', {'message': message})

    weather = get_weather(location)

    if not weather:
        message = {
            'style': 'danger',
            'headline': 'Weather API error',
            'description': 'Request for weather data failed. Please try again later.'
        }
        return render(request, 'weather_app/pages/weather_dashboard.html', {'message': message})

    weather = convert_timestamps_to_datetime(weather)

    chart_data = get_chart_data(weather)

    return render(request, 'weather_app/pages/weather_dashboard.html',
                  {'location': location, 'weather': weather, 'chart_data': chart_data})


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
