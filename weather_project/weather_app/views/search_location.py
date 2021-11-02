from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from requests.exceptions import Timeout
import json
import pprint

def search_location(request):
    def get_search_results(search_query):
        # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/search/get
        try:
            url = 'https://api.openrouteservice.org/geocode/search'
            params = {
                'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
                'size': 20,
                'text': search_query}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                search_results = response.json()['features']
                return search_results  # SUCCESS
            else:  # FAIL
                messages.error(request, {
                    'header': 'Location service error',
                    'description': 'Request for location data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_search_results(search_query)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'HTTP status: {response.status_code}']})
                return None
        except Timeout as err:
            messages.warning(
                request, {
                    'header': 'Location service time out',
                    'description': 'Please try it again later...',
                    'icon': 'fas fa-hourglass-end',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_search_results(search_query)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {err}']})
            return None
    try:
        search_query = request.GET.get('search_query')
        search_results = get_search_results(search_query)
        if not search_results:
            return render(request, 'weather_app/dashboard.html')
        if len(search_results) == 0:
            messages.warning(
                request, {
                    'header': 'Location not found',
                    'description': 'You probably entered the name of the location incorrectly. Please try it again.',
                    'icon': 'bi bi-geo-alt-fill',
                    'show_search_form': True})
            return render(request, 'weather_app/dashboard.html')
        elif len(search_results) == 1:
            location = search_results[0]
            base_url = reverse('dashboard')
            params = urlencode({
                'latitude': location['geometry']['coordinates'][1],
                'longitude': location['geometry']['coordinates'][0],
                'label': location['properties']['label']})
            uri = f'{base_url}?{params}'
            return redirect(uri)  # SUCCESS => rerdirect to Dashboard
        elif len(search_results) > 1:  # SUCCESS => show search results
            if len(search_results) == 20:
                description = 'Showing only first 20 matching locations:'
            else:
                description = None
            messages.success(
                request, {
                    'header': 'Select location',
                    'description': description,
                    'icon': 'bi bi-geo-alt-fill',
                    'search_results': search_results,
                    'show_search_form': True})
            return render(request, 'weather_app/dashboard.html')
    except Exception as err:
        messages.error(request, {
            'header': 'Internal error',
            'description': 'Location search failed.',
            'icon': 'fas fa-times-circle',
            'admin_details': [
                'Method: search_location(request)',
                f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')
