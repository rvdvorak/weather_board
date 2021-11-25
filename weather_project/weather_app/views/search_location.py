from requests.exceptions import Timeout, HTTPError
from django.contrib import messages
import pprint
from weather_app.views.utils import get_location_history, get_favorite_locations, redirect_to_dashboard, render_dashboard
from weather_app.views.API_keys import ORS_key
import requests


def get_search_results(search_query, ORS_key, timeout=5, max_count=20):
    # https://openrouteservice.org/dev/#/api-docs/geocode/search/get
    url = 'https://api.openrouteservice.org/geocode/search'
    params = {
        'api_key': ORS_key,
        'size': max_count,
        'text': search_query}
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()['features']


def search_location(request):
    max_count = 20
    search_query = request.GET.get('search_query')
    if search_query in ['', None]:
        # TODO Test search location without search text
        # Missing search text
        messages.warning(
            request, {
                'header': 'Nothing to search',
                'description': 'First enter the name of the location to search.',
                'icon': 'bi bi-geo-alt-fill',
                'show_search_form': True})
        return render_dashboard(request)
    try:
        search_results = get_search_results(
            search_query, ORS_key, max_count=20)
    except Timeout as err:
        # API request time out
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
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
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    if len(search_results) == 0:
        # TODO Test search location not found
        # Location not found
        messages.warning(
            request, {
                'header': 'Location not found',
                'description': f'"{search_query}" may not be the correct location name. Please type something else.',
                'icon': 'bi bi-geo-alt-fill',
                'show_search_form': True})
        return render_dashboard(request)
    elif len(search_results) == 1:
        # TODO Test search location with single match
        # Single match => rerdirect to Dashboard
        return redirect_to_dashboard({
            'latitude': search_results[0]['geometry']['coordinates'][1],
            'longitude': search_results[0]['geometry']['coordinates'][0],
            'label': search_results[0]['properties']['label']})
    elif len(search_results) > 1:
        # TODO Test search location with multiple matches
        # Multiple matches => show search results in message
        if len(search_results) == max_count:
            # TODO Test search location with too many matches
            # Too many matches
            message_description = f'Showing only first {max_count} matching locations:'
        else:
            message_description = None
        messages.success(
            request, {
                'header': 'Select location',
                'description': message_description,
                'icon': 'bi bi-geo-alt-fill',
                'search_results': search_results,
                'show_search_form': True})
        return render_dashboard(request)
