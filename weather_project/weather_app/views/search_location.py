from requests.exceptions import Timeout, HTTPError
from django.contrib import messages
from weather_app.views.utils import get_location_query, redirect_to_dashboard, render_dashboard
import requests
import pprint
from django.conf import settings

ORS_KEY = settings.ORS_KEY


def get_search_results(search_text, ORS_KEY, ORS_timeout, max_count):
    # Obtain list of locations matching the search text
    # using the Open Route Service free API:
    # https://openrouteservice.org/dev/#/api-docs/geocode/search/get
    url = 'https://api.openrouteservice.org/geocode/search'
    params = {
        'api_key': ORS_KEY,
        'size': max_count,
        'text': search_text}
    response = requests.get(url, params=params, timeout=ORS_timeout)
    response.raise_for_status()
    matching_locations = response.json()['features']
    search_results = []
    if not len(matching_locations) == 0:
        labels = set([])
        for item in matching_locations:
            if not item['properties']['label'] in labels:
                search_results.append({
                    'label': item['properties']['label'],
                    'latitude': item['geometry']['coordinates'][1],
                    'longitude': item['geometry']['coordinates'][0]})
            labels.add(item['properties']['label'])
    return search_results


def search_location(request, ORS_KEY=ORS_KEY, ORS_timeout=5, max_count=20):
    # Handle the location search process.
    # Location search is available on all pages.
    query = get_location_query(request)
    if not query['search_text']:
        # Nothing to search
        return redirect_to_dashboard(query)
    try:
        search_results = get_search_results(
            query['search_text'], ORS_KEY, ORS_timeout, max_count)
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
        query.update(search_results[0])
        query.pop('search_text')
        return redirect_to_dashboard(query)
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
