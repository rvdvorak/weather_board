from requests.exceptions import Timeout, HTTPError
from django.contrib import messages
import pprint
from weather_app.views.utils import redirect_to_dashboard, get_favorite_locations, get_location_history, render_dashboard
from weather_app.views.API_keys import ORS_key
import random
import requests


def get_random_location_params(ORS_key, ORS_timeout):
    # https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get
    url = 'https://api.openrouteservice.org/geocode/reverse'
    latitude = round(
        random.random() * 180 - 90,
        6)
    longitude = round(
        random.random() * 360 - 180,
        6)
    params = {
        'api_key': ORS_key,
        'point.lat': latitude,
        'point.lon': longitude,
        'size': 1}
    response = requests.get(url, params=params, timeout=ORS_timeout)
    response.raise_for_status()
    return {
        'latitude': latitude,
        'longitude': longitude,
        'label': response.json()['features'][0]['properties']['label']}


def random_location(request, ORS_key=ORS_key, ORS_timeout=5):
    user = request.user
    try:
        location_params = get_random_location_params(ORS_key, ORS_timeout)
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Location service error',
                'description': 'Communication with location service failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    return redirect_to_dashboard(location_params)
