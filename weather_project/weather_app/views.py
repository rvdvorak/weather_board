from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from datetime import datetime
from urllib.parse import urlencode
import requests
import pprint
import json
import random


def home(request):
    return render(request, 'weather_app/home.html')


def dashboard(request):
    def get_location(request):
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        label = request.GET.get('label')
        if not (latitude and longitude and label):
            return {
                'data': None,
                'message': {
                    'style': 'lightblue',
                    'headline': 'Select location',
                    'description': 'Search location to get started.',
                    'show_search_form': True,
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
                    'description': 'Location data type error. Try to search location',
                    'show_search_form': True,
                }
            }
        if not (-90 <= latitude <= 90):
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect coordinates',
                    'description': 'Latitude out of range. Try to search location',
                    'show_search_form': True,
                }
            }
        if not (-180 <= longitude <= 180):
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incorrect coordinates',
                    'description': 'Longitude out of range. Try to search location',
                    'show_search_form': True,
                }
            }
        if label == '':
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Incomplete location data',
                    'description': 'Missing location label. Try to search location',
                    'show_search_form': True,
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
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            print('-' * 80)
            print('API endpoint: ', url)
            print('Exception: ', err)
            print('-' * 80)
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Weather service not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': False,
                }
            }
        if not response.status_code == 200:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Weather API error',
                    'description': f'OpenWeatherMap.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        weather = response.json()

        # Convert Unix timestamps to datetime
        weather['current']['dt'] = datetime.fromtimestamp(
            weather['current']['dt'])
        weather['current']['sunrise'] = datetime.fromtimestamp(
            weather['current']['sunrise'])
        weather['current']['sunset'] = datetime.fromtimestamp(
            weather['current']['sunset'])

        if 'minutely' in weather:
            for minute in range(len(weather['minutely'])):
                weather['minutely'][minute]['dt'] = datetime.fromtimestamp(
                    weather['minutely'][minute]['dt'])

        if 'hourly' in weather:
            for hour in range(len(weather['hourly'])):
                weather['hourly'][hour]['dt'] = datetime.fromtimestamp(
                    weather['hourly'][hour]['dt'])

        if 'daily' in weather:
            for day in range(len(weather['daily'])):
                weather['daily'][day]['dt'] = datetime.fromtimestamp(
                    weather['daily'][day]['dt'])
                weather['daily'][day]['sunrise'] = datetime.fromtimestamp(
                    weather['daily'][day]['sunrise'])
                weather['daily'][day]['sunset'] = datetime.fromtimestamp(
                    weather['daily'][day]['sunset'])

        if 'alerts' in weather:
            for alert in range(len(weather['alerts'])):
                weather['alerts'][alert]['start'] = datetime.fromtimestamp(
                    weather['alerts'][alert]['start'])
                weather['alerts'][alert]['end'] = datetime.fromtimestamp(
                    weather['alerts'][alert]['end'])

        return {
            'data': weather,
        }

    def get_air_pollution(location):
        url = 'http://api.openweathermap.org/data/2.5/air_pollution'
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'appid': '6fe37effcfa866ecec5fd235699a402d',
        }
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            print('-' * 80)
            print('API endpoint: ', url)
            print('Exception: ', err)
            print('-' * 80)
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Weather service not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': False,
                }
            }
        if not response.status_code == 200:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Air pollution API error',
                    'description': f'OpenWeatherMap.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        current = response.json()['list'][0]
        current['dt'] = datetime.fromtimestamp(current['dt'])

        url = 'http://api.openweathermap.org/data/2.5/air_pollution/forecast'
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'appid': '6fe37effcfa866ecec5fd235699a402d',
        }
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            print('-' * 80)
            print('API endpoint: ', url)
            print('Exception: ', err)
            print('-' * 80)
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Weather service not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': False,
                }
            }
        if not response.status_code == 200:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Air pollution API error',
                    'description': f'OpenWeatherMap.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        forecast = response.json()['list']
        for hour in range(len(forecast)):
            forecast[hour]['dt'] = datetime.fromtimestamp(forecast[hour]['dt'])

        aqi_stars = {
            1: [
                'fas fa-star',
                'fas fa-star',
                'fas fa-star',
                'fas fa-star',
                'fas fa-star',
            ],
            2: [
                'fas fa-star',
                'fas fa-star',
                'fas fa-star',
                'fas fa-star',
                'far fa-star',
            ],
            3: [
                'fas fa-star',
                'fas fa-star',
                'fas fa-star',
                'far fa-star',
                'far fa-star',
            ],
            4: [
                'fas fa-star',
                'fas fa-star',
                'far fa-star',
                'far fa-star',
                'far fa-star',
            ],
            5: [
                'fas fa-star',
                'far fa-star',
                'far fa-star',
                'far fa-star',
                'far fa-star',
            ],
        }

        current['main']['aqi_stars'] = aqi_stars[current['main']['aqi']]

        return {
            'data': {
                'current': current,
                'forecast': forecast,
            }
        }

    def get_chart_data(weather):
        if not 'minutely' in weather:
            return None
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
        return render(request, 'weather_app/message.html', {'message': location['message']})

    weather = get_weather(location['data'])
    if not weather['data']:
        return render(request, 'weather_app/message.html', {'message': weather['message']})

    air_pollution = get_air_pollution(location['data'])
    if not air_pollution['data']:
        return render(request, 'weather_app/message.html', {'message': air_pollution['message']})

    chart_data = get_chart_data(weather['data'])

    return render(request, 'weather_app/dashboard.html',
                  {
                      'location': location['data'],
                      'weather': weather['data'],
                      'air_pollution': air_pollution['data'],
                      'chart_data': chart_data,
                  }
                  )


def search_location(request):
    search_text = request.GET.get('search_text')
    if not search_text:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'warning',
                'headline': 'Search location',
                'description': 'First enter the name of the location to search.',
                'show_search_form': True,
                }
            }
        )
    
    try:
        search_text = str(search_text)
    except:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'warning',
                'headline': 'Search location',
                'description': 'First enter the name of the location to search.',
                'show_search_form': True,
                }
            }
        )

    url='https://api.openrouteservice.org/geocode/search'
    params={
        'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
        'size': 20,
        'text': search_text,
    }
    try:
        response = requests.get(url, params=params, timeout=5)
    except Exception as err:
        print('-' * 80)
        print('API endpoint: ', url)
        print('Exception: ', err)
        print('-' * 80)
        return {
            'data': None,
            'message': {
                'style': 'danger',
                'headline': 'Location service not responding',
                'description': 'Please try it again later...',
                'show_search_form': False,
            }
        }
    if not response.status_code == 200:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'danger',
                'headline': 'Location search failed',
                'description': f'OpenRouteService.org status: {response.status_code}',
                'show_search_form': False,
                }
            }
        )
    found_locations=response.json()['features']
    if not found_locations:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'warning',
                'headline': 'No location found',
                'description': 'You probably entered the name of the location incorrectly. Please try again.',
                'show_search_form': True,
                }
            }
        )
    return render(request, 'weather_app/message.html', {
        'message': {
            'style': 'success',
            'headline': 'Select location',
            'description': None,
            'found_locations': found_locations,
            'show_search_form': True,
            }
        }
    )


def random_location(request):
    def get_random_loaction():
        latitude=(random.random() * 180) - 90
        longitude=(random.random() * 360) - 180
        url='https://api.openrouteservice.org/geocode/reverse'
        params={
            'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
            'point.lat': latitude,
            'point.lon': longitude,
            'size': 1,
        }
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            print('-' * 80)
            print('API endpoint: ', url)
            print('Exception: ', err)
            print('-' * 80)
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Location service not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': False,
                }
            }
        if not response.status_code == 200:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Location API error',
                    'description': f'OpenRouteService.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        try:
            location=response.json()['features'][0]
            return {
                'data': {
                    'latitude': location['geometry']['coordinates'][1],
                    'longitude': location['geometry']['coordinates'][0],
                    'label': location['properties']['label'],
                }
            }
        except:
            return {
                'data': None,
                'message': {
                    'style': 'danger',
                    'headline': 'Random location error',
                    'description': 'Sorry, something went wrong...',
                    'show_search_form': False,
                }
            }

    location=get_random_loaction()
    if not location['data']:
        return render(request, 'weather_app/message.html', {'message': location['message']})
    base_url=reverse('dashboard')
    query_string=urlencode(
        {
            'latitude': location['data']['latitude'],
            'longitude': location['data']['longitude'],
            'label': location['data']['label'],
        }
    )
    url=f'{base_url}?{query_string}'
    print('URL', url)
    response=redirect(url)
    return response
