from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
import requests
import json
import random

#TODO: Exceptions

def random_location(request):
    def get_random_loaction():
        latitude = (random.random() * 180) - 90
        longitude = (random.random() * 360) - 180
        url = 'https://api.openrouteservice.org/geocode/reverse'
        params = {
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
                    'style': 'warning',
                    'headline': 'Location service is not responding',
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
            location = response.json()['features'][0]
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

    location = get_random_loaction()
    if not location['data']:
        return render(request, 'weather_app/message.html', {'message': location['message']})
    base_url = reverse('dashboard')
    query_string = urlencode(
        {
            'latitude': location['data']['latitude'],
            'longitude': location['data']['longitude'],
            'label': location['data']['label'],
        }
    )
    uri = f'{base_url}?{query_string}'
    return redirect(uri)
