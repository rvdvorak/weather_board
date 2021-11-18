from django.shortcuts import render
from django.contrib import messages
from requests.exceptions import Timeout, HTTPError
from django.core.exceptions import ValidationError
import pprint
import pytz
from weather_app.views.utils import get_location_params, get_location_instance, get_weather, get_air_pollution, get_charts, render_dashboard
from weather_app.views.API_keys import OWM_key
# Persist sample data for testing
import pickle


# TODO Sunrise/Sunset: http://127.0.0.1:8000/?latitude=81.475139&longitude=-161.169992&label=Arctic+Ocean


# TODO Tests
def dashboard(request):
    user = request.user
    location_params = get_location_params(request)
    try:
        location = get_location_instance(location_params, user)
    except ValidationError as err:
        messages.error(
            request, {
                'header': 'Incorrect location parameters',
                'description': 'Try to search the location by its name.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    if not location:
        return render_dashboard(request)
    try:
        weather = get_weather(location, OWM_key)
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/weather.pkl', 'wb') as file:
        #     pickle.dump(weather, file)
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Weather service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Weather service error',
                'description': 'Communication with weather server failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    timezone = pytz.timezone(weather['timezone'])
    try:
        air_pollution = get_air_pollution(location, timezone, OWM_key)
        # Persist sample data for testing
        # with open('weather_app/tests/sample_data/air_pollution.pkl', 'wb') as file:
        #     pickle.dump(air_pollution, file)
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Air pollution service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Air pollution service error',
                'description': 'Communication with air pollution server failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    charts = get_charts(weather)
    # Persist sample data for testing
    # with open('weather_app/tests/sample_data/charts.pkl', 'wb') as file:
    #     pickle.dump(charts, file)
    if user.is_authenticated:
        location.save()
    return render_dashboard(
        request,
        location=location,
        weather=weather,
        air_pollution=air_pollution,
        charts=charts)
