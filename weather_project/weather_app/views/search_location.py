from requests.exceptions import Timeout, HTTPError
from django.template.response import TemplateResponse
from django.contrib import messages
from weather_app.views.utils import get_query, get_location_history, get_favorite_locations, redirect_to_dashboard, render_dashboard
from weather_app.views.API_keys import ORS_key
import requests
import pprint


def get_search_results(search_text, ORS_key, ORS_timeout, max_count):
    # Get list of matching locations from Open Route Service free API:
    # https://openrouteservice.org/dev/#/api-docs/geocode/search/get
    url = 'https://api.openrouteservice.org/geocode/search'
    params = {
        'api_key': ORS_key,
        'size': max_count,
        'text': search_text}
    response = requests.get(url, params=params, timeout=ORS_timeout)
    response.raise_for_status()
    json_items = response.json()['features']
    search_results = []
    if not len(json_items) == 0:
        for item in json_items:
            search_results.append({
                'label': item['properties']['label'],
                'latitude': item['geometry']['coordinates'][1],
                'longitude': item['geometry']['coordinates'][0]})
    return search_results


def search_location(request, ORS_key=ORS_key, ORS_timeout=5, max_count=20):
    # Handle the location search process.
    # Location search is available on every page.
    query = get_query(request)
    query['search_text'] = request.GET.get('search_text')
    if not query['search_text']:
        # Nothing to search
        return redirect_to_dashboard(query)
    try:
        search_results = get_search_results(
            query['search_text'], ORS_key, ORS_timeout, max_count)
    except Timeout as err:
        # API request time out
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'search_results': None,
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        # API request failed
        messages.error(
            request, {
                'header': 'Location service error',
                'description': 'Communication with location service failed.',
                'icon': 'fas fa-times-circle',
                'search_results': None,
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    if len(search_results) == 0:
        # Location not found
        messages.warning(
            request, {
                'header': 'Location not found',
                'description': f"\"{query['search_text']}\" may not be the correct location name.",
                'icon': 'bi bi-geo-alt-fill',
                'search_results': None,
                'show_search_form': True})
        return render_dashboard(request)
    elif len(search_results) == 1:
        # Single match => rerdirect to Dashboard
        return redirect_to_dashboard({
            'display_mode': query['display_mode'],
            'label': search_results[0]['label'],
            'latitude': search_results[0]['latitude'],
            'longitude': search_results[0]['longitude']})
    elif len(search_results) > 1:
        # Multiple matches => show search results in message
        description = None
        if len(search_results) == max_count:
            # Too many matches
            description = f'Showing only first {max_count} matching locations:'
        messages.success(
            request, {
                'header': 'Select location',
                'description': description,
                'icon': 'bi bi-geo-alt-fill',
                'search_results': search_results,
                'show_search_form': True})
        return render_dashboard(request)
