from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
import requests
import json
import random
import pprint

#TODO Implement Django Messages

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
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Obtaining random location failed.',
                    'admin_details': [
                        'Method: get_random_location()',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            response = requests.get(url, params=params, timeout=5)
        except Exception as err:
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Location service is not responding',
                    'description': 'Please try it again later...',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_random_location()',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            if not response.status_code == 200:
                raise Exception('HTTP response failed.')
            location = response.json()['features'][0]
            latitude = location['geometry']['coordinates'][1]
            longitude = location['geometry']['coordinates'][0]
            label = location['properties']['label']
            return {
                'data': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'label': label}}
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Location service error',
                    'description': 'Request for location data failed.',
                    'admin_details': [
                        'Method: get_random_location()',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'HTTP status: {response.status_code}',
                        f'Exception: {pprint.pformat(err)}']}}
    
    try:
        location = get_random_location()
        if not 'data' in location:
            return render(request, 'weather_app/message.html', {
                'message': location['message']})
        base_url = reverse('dashboard')
        query_string = urlencode({
            'latitude': location['data']['latitude'],
            'longitude': location['data']['longitude'],
            'label': location['data']['label']})
        uri = f'{base_url}?{query_string}'
        return redirect(uri)
    except Exception as err:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'danger',
                'headline': 'Internal error',
                'description': 'Processing random location failed.',
                'admin_details': [
                    'Method: random_location(request)',
                    f'Exception: {pprint.pformat(err)}']}})
        
