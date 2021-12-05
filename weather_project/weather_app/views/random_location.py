from requests.exceptions import Timeout, HTTPError
from django.contrib import messages
import pprint
from weather_app.views.utils import get_query, redirect_to_dashboard, get_favorite_locations, get_location_history, render_dashboard
from weather_app.views.API_keys import ORS_key
from random import random
import requests


def get_random_location_params(ORS_key, ORS_timeout):
    # Generates random coordinates and returns matching location
    # using the Open Route Service free API:
    # https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get
    latitude = round(random() * 180 - 90, 6)
    longitude = round(random() * 360 - 180, 6)
    params = {
        'api_key': ORS_key,
        'point.lat': latitude,
        'point.lon': longitude,
        'size': 1}
    url = 'https://api.openrouteservice.org/geocode/reverse'
    response = requests.get(url, params=params, timeout=ORS_timeout)
    response.raise_for_status()
    location = response.json()['features'][0]
    return {
        'latitude': location['geometry']['coordinates'][1],
        'longitude': location['geometry']['coordinates'][0],
        'label': location['properties']['label']}


def random_location(request, ORS_key=ORS_key, ORS_timeout=5):
    # Show weather forecast for random location
    query = get_query(request)
    try:
        location = get_random_location_params(ORS_key, ORS_timeout)
    except Timeout as err:
        # Location API timeout
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        # Location API request failed
        messages.error(
            request, {
                'header': 'Location service error',
                'description': 'Communication with location service failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    query.update(location)
    # Show weather forecast for the location
    return redirect_to_dashboard(query)
