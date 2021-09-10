from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
import requests
import json


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

    url = 'https://api.openrouteservice.org/geocode/search'
    params = {
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
                'style': 'warning',
                'headline': 'Location service is not responding',
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
    found_locations = response.json()['features']
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
    if len(found_locations) == 1:
        base_url = reverse('dashboard')
        query_string = urlencode(
            {
                'latitude': found_locations[0]['geometry']['coordinates'][1],
                'longitude': found_locations[0]['geometry']['coordinates'][0],
                'label': found_locations[0]['properties']['label'],
            }
        )
        uri = f'{base_url}?{query_string}'
        return redirect(uri)        
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