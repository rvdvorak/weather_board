from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
from requests.exceptions import Timeout
import requests
import json
import pprint


def search_location(request):
    def get_search_text(request):
        try:
            search_text = request.GET.get('search_text')
            if (search_text == '') or (search_text == None):
                messages.warning(
                    request, {
                        'headline': 'Nothing to search',
                        'description': 'First enter the name of the location to search:',
                        'icon': 'fas fa-exclamation-triangle',
                        'show_search_form': True,
                        'admin_details': [
                            'Method: get_search_text(request)',
                            f'search_text: {pprint.pformat(search_text)}']})
                return None
            return search_text
        except Exception as err:
            messages.error(
                request, {
                    'headline': 'Internal error',
                    'description': 'Location search failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_search_text(request)',
                        f'Exception: {pprint.pformat(err)}']})
            return None

    def get_search_results(search_text):
        # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/search/get
        try:
            url = 'https://api.openrouteservice.org/geocode/search'
            params = {
                'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
                'size': 20,
                'text': search_text}
            response = requests.get(url, params=params, timeout=5)
            if not response.status_code == 200:
                messages.error(request, {
                    'headline': 'Location service error',
                    'description': 'Request for location data failed.',
                    'icon': 'fas fa-times-circle',
                    'admin_details': [
                        'Method: get_search_results(search_text)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'HTTP status: {response.status_code}']})
                return None
            found_locations = response.json()['features']
            return found_locations
        except Timeout as err:
            messages.warning(request, {
                'headline': 'Location service time out',
                'description': 'Please try it again later...',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': [
                    'Method: get_search_results(search_text)',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'Exception: {err}']})
            return None
        except Exception as err:
            messages.error(request, {
                'headline': 'Internal error',
                'description': 'Location search failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: get_search_results(search_text)',
                    f'API endpoint: {url}',
                    f'Parameters: {pprint.pformat(params)}',
                    f'Exception: {pprint.pformat(err)}']})
            return None

    try:
        search_text = get_search_text(request)
        if search_text == None:
            return render(request, 'weather_app/message.html')
        search_results = get_search_results(search_text)
        if search_results == None:
            return render(request, 'weather_app/message.html')
        if len(search_results) == 0:
            messages.warning(
                request, {
                'headline': 'No location found',
                    'description': 'You probably entered the name of the location incorrectly. Please try it again.',
                    'icon': 'fas fa-exclamation-triangle',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: search_location(request)',
                        f'search_text: {pprint.pformat(search_text)}']})
            return render(request, 'weather_app/message.html')
        if len(search_results) == 1:
            location = search_results[0]
            base_url = reverse('dashboard')
            query_string = urlencode({
                'latitude': location['geometry']['coordinates'][1],
                'longitude': location['geometry']['coordinates'][0],
                'label': location['properties']['label']})
            uri = f'{base_url}?{query_string}'
            return redirect(uri)
        if len(search_results) == 20:
            message_description = 'Showing only first 20 matching locations:'
        else:
            message_description = None
        messages.success(
            request, {
                'headline': 'Select location',
                'description': message_description,
                'icon': 'fas fa-check-circle',
                'found_locations': search_results,
                'show_search_form': True})
        return render(request, 'weather_app/message.html')
    except Exception as err:
        messages.error(request, {
            'headline': 'Internal error',
            'description': 'Location search failed.',
            'icon': 'fas fa-times-circle',
            'admin_details': [
                'Method: search_location(request)',
                f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
