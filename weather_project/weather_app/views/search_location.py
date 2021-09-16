from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
import requests
import json
import pprint


def search_location(request):
    def get_search_text(request):
        try:
            search_text = str(request.GET.get('search_text'))
            if search_text == '':
                raise Exception('search_text is empty')
        except Exception as err:
            return {
                'message': {
                    'style': 'warning',
                    'headline': 'Search location',
                    'description': 'First enter the name of the location to search.',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: get_search_text(request)',
                        f'Exception: {pprint.pformat(err)}']}}
        return {'data': search_text}

    def get_search_results(search_text):
        # API docs: https://openrouteservice.org/dev/#/api-docs/geocode/search/get
        url = 'https://api.openrouteservice.org/geocode/search'
        params = {
            'api_key': '5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71',
            'size': 20,
            'text': search_text}
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
                        'Method: get_search_results(search_text)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']}}
        if not response.status_code == 200:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Location search error',
                    'description': 'Request for location data failed.',
                    'admin_details': [
                        'Method: get_search_results(search_text)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']}}
        try:
            found_locations = response.json()['features']
        except Exception as err:
            return {
                'message': {
                    'style': 'danger',
                    'headline': 'Internal error',
                    'description': 'Unexpected data structure.',
                    'admin_details': [
                        'Method: get_search_results(search_text)',
                        f'API endpoint: {url}',
                        f'Parameters: {pprint.pformat(params)}',
                        f'Exception: {pprint.pformat(err)}']}}
        return {'data': found_locations}

    try:
        search_text = get_search_text(request)
        if not 'data' in search_text:
            return render(request, 'weather_app/message.html', {
                'message': search_text['message']})
        search_results = get_search_results(search_text['data'])
        if not 'data' in search_results:
            return render(request, 'weather_app/message.html', {
                'message': search_results['message']})
        if len(search_results['data']) == 0:
            return render(request, 'weather_app/message.html', {
                'message': {
                    'style': 'warning',
                    'headline': 'No location found',
                    'description': 'You probably entered the name of the location incorrectly. Please try again.',
                    'show_search_form': True,
                    'admin_details': [
                        'Method: search_location(request)',
                        f'search_text: {pprint.pformat(search_text)}',
                        f'search_results: {pprint.pformat(search_results)}']}})
        if len(search_results['data']) == 1:
            location = search_results['data'][0]
            base_url = reverse('dashboard')
            query_string = urlencode({
                'latitude': location['geometry']['coordinates'][1],
                'longitude': location['geometry']['coordinates'][0],
                'label': location['properties']['label']})
            uri = f'{base_url}?{query_string}'
            return redirect(uri)
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'success',
                'headline': 'Select location',
                'found_locations': search_results['data'],
                'show_search_form': True}})
    except Exception as err:
        return render(request, 'weather_app/message.html', {
            'message': {
                'style': 'danger',
                'headline': 'Internal error',
                'description': 'Location search failed.',
                'admin_details': [
                    'Method: search_location(request)',
                    f'Exception: {pprint.pformat(err)}']}})
