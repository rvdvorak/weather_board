from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from requests.exceptions import Timeout
import json
import pprint
import random


def random_location(request):
    # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get
    try:
        url = 'https://api.openrouteservice.org/geocode/reverse'
        latitude = random.random() * 180 - 90
        latitude = round(latitude, 6)
        longitude = random.random() * 360 - 180
        longitude = round(longitude, 6)
        params = {
            'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
            'point.lat': latitude,
            'point.lon': longitude,
            'size': 1}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            label = response.json()['features'][0]['properties']['label']
            base_url = reverse('dashboard')
            params = urlencode({
                'latitude': latitude,
                'longitude': longitude,
                'label': label})
            uri = f'{base_url}?{params}'
            return redirect(uri)  # SUCCESS
        else:  # FAIL
            messages.error(request, {
                'header': 'Location service error',
                'description': 'Request for location data failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Meth()',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'HTTP status: {response.status_code}']})
            return render(request, 'weather_app/dashboard.html')
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again later...',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': [
                    'Meth()',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'Exception: {err}']})
        return render(request, 'weather_app/dashboard.html')
    except Exception as err:
        messages.error(request, {
            'header': 'Internal error',
            'description': 'Processing random location failed.',
            'icon': 'fas fa-times-circle',
            'admin_details': [
                'Meth()',
                f'API endpoint: {url}',
                f'Parameters: {pprint.pformat(params)}',
                f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')
