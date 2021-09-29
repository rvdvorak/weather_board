from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
from requests.exceptions import Timeout
import requests
import json
import random
import pprint


def random_location(request):
    def get_random_location():
        # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get
        try:
            url = 'https://api.openrouteservice.org/geocode/reverse'
            latitude = (random.random() * 180) - 90
            longitude = (random.random() * 360) - 180
            params = {
                'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
                'point.lat': latitude,
                'point.lon': longitude,
                'size': 1}
            response = requests.get(url, params=params, timeout=5)
            if not response.status_code == 200:
                messages.error(request, {
                    'headline': 'Location service error',
                    'description': 'Request for location data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_random_location()',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'HTTP status: {response.status_code}']})
                return None
            location = response.json()['features'][0]
            latitude = location['geometry']['coordinates'][1]
            longitude = location['geometry']['coordinates'][0]
            label = location['properties']['label']
            return {
                'latitude': latitude,
                'longitude': longitude,
                'label': label}
        except Timeout as err:
            messages.warning(request, {
                'headline': 'Location service time out',
                'description': 'Please try it again later...',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': [
                    'Method: get_random_location()',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'Exception: {err}']})
            return None
        except Exception as err:
            messages.error(request, {
                'headline': 'Internal error',
                'description': 'Obtaining random location failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: get_random_location()',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'Exception: {pprint.pformat(err)}']})
            return None

    try:
        location = get_random_location()
        if location == None:
            return render(request, 'weather_app/message.html')
        base_url = reverse('dashboard')
        query_string = urlencode({
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'label': location['label']})
        uri = f'{base_url}?{query_string}'
        return redirect(uri)
    except Exception as err:
        messages.error(request, {
            'headline': 'Internal error',
            'description': 'Processing random location failed.',
            'icon': 'fas fa-times-circle',
            'admin_details': [
                'Method: random_location(request)',
                f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
        
