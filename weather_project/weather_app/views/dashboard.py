from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import requests
import json
import pprint

#TODO: Exceptions

def dashboard(request):
    def get_location(request):
        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
            label = str(request.GET.get('label'))
        except:
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Missing or incorrect location data',
                    'description': 'Try to search the location.',
                    'show_search_form': True,
                }
            }
        if not (-90 <= latitude <= 90) and (-180 <= longitude <= 180):
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Incorrect location',
                    'description': 'Coordinates out of range. Try to search the location.',
                    'show_search_form': True,
                }
            }
        if label == '':
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Incomplete location data',
                    'description': 'Missing location label. Try to search the location.',
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
                'message': {
                    'style': 'warning',
                    'headline': 'Weather service is not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': True,
                }
            }
        if not response.status_code == 200:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Weather API error',
                    'description': f'OpenWeatherMap.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        weather = response.json()

        # Convert Unix timestamps to datetime
        try:
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

            for hour in range(len(weather['hourly'])):
                weather['hourly'][hour]['dt'] = datetime.fromtimestamp(
                    weather['hourly'][hour]['dt'])

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
        except:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Timestamp conversion failed.',
                    'show_search_form': False,
                }
            }

    def get_air_pollution(location):
        #TODO: Remove API endpoint
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
                'message': {
                    'style': 'warning',
                    'headline': 'Weather service is not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': True,
                }
            }
        if not response.status_code == 200:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Air pollution API error',
                    'description': f'OpenWeatherMap.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        current = response.json()['list'][0]
        current['dt'] = datetime.fromtimestamp(current['dt'])
        print('*' * 80)
        print('current[0]:', current['dt'])
        print('*' * 80)

        #TODO: Keep only air_pollution/forecast
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
                'message': {
                    'style': 'warning',
                    'headline': 'Weather service is not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': True,
                }
            }
        if not response.status_code == 200:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Air pollution API error',
                    'description': f'OpenWeatherMap.org status: {response.status_code}',
                    'show_search_form': False,
                }
            }
        forecast = response.json()['list']
        print('*' * 80)
        print('forecast[0]:', datetime.fromtimestamp(forecast[0]['dt']))
        print('*' * 80)
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

    def add_chart_data(weather):
        if 'minutely' in weather:
            minutely_chart = {
                'time': [],
                'volume': [],
            }
            for minute in weather['minutely']:
                minutely_chart['time'].append(minute['dt'].strftime("%H:%M"))
                minutely_chart['volume'].append(round(minute['precipitation'], 1))
            weather['minutely_chart'] = minutely_chart
        return weather

    location = get_location(request)
    if not 'data' in location:
        return render(request, 'weather_app/message.html', {'message': location['message']})

    weather = get_weather(location['data'])
    if not 'data' in weather:
        return render(request, 'weather_app/message.html', {'message': weather['message']})

    air_pollution = get_air_pollution(location['data'])
    if not 'data' in air_pollution:
        return render(request, 'weather_app/message.html', {'message': air_pollution['message']})

    weather['data'] = add_chart_data(weather['data'])

    print('+' * 80)
    pprint.pprint(weather)
    print('+' * 80)


    return render(request, 'weather_app/dashboard.html', {
        'location': location['data'],
        'weather': weather['data'],
        'air_pollution': air_pollution['data'],
    }
    )
