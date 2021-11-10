from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from requests.exceptions import Timeout, HTTPError
from django.core.exceptions import ValidationError
import pprint
from .utils import *

# TODO Sunrise/Sunset: http://127.0.0.1:8000/?latitude=81.475139&longitude=-161.169992&label=Arctic+Ocean

def dashboard(request):
    user = request.user
    weather = None
    air_pollution = None
    charts = None
    location = get_location_instance(get_location_params(request), user)
    if location:
        try:
            weather = get_weather(location)
        except Timeout as err:
            messages.warning(
                request, {
                    'header': 'Weather service time out',
                    'description': 'Please try it again later...',
                    'icon': 'fas fa-hourglass-end',
                    'show_search_form': True,
                    'admin_details': [
                        f'Exception: {pprint.pformat(err)}']})
            return render(
                request,
                'weather_app/dashboard.html', {
                    'location_history': get_location_history(user),
                    'favorite_locations': get_favorite_locations(user)})
        except HTTPError as err:
            messages.error(
                request, {
                    'header': 'Weather service error',
                    'description': 'Communication with weather service failed.',
                    'icon': 'fas fa-times-circle',
                    'show_search_form': True,
                    'admin_details': [
                        f'Exception: {pprint.pformat(err)}']})
            return render(
                request,
                'weather_app/dashboard.html', {
                    'location_history': get_location_history(user),
                    'favorite_locations': get_favorite_locations(user)})
        timezone = pytz.timezone(weather['timezone'])
        try:
            air_pollution = get_air_pollution(location, timezone)
        except Timeout as err:
            messages.warning(
                request, {
                    'header': 'Air pollution service time out',
                    'description': 'Please try it again later...',
                    'icon': 'fas fa-hourglass-end',
                    'show_search_form': True,
                    'admin_details': [
                        f'Exception: {pprint.pformat(err)}']})
            return render(
                request,
                'weather_app/dashboard.html', {
                    'location_history': get_location_history(user),
                    'favorite_locations': get_favorite_locations(user)})
        except HTTPError as err:
            messages.error(
                request, {
                    'header': 'Air pollution service error',
                    'description': 'Communication with Air pollution service failed.',
                    'icon': 'fas fa-times-circle',
                    'show_search_form': True,
                    'admin_details': [
                        f'Exception: {pprint.pformat(err)}']})
            return render(
                request,
                'weather_app/dashboard.html', {
                    'location_history': get_location_history(user),
                    'favorite_locations': get_favorite_locations(user)})
        charts = get_charts(weather)
        if user.is_authenticated:
            location.save()
    if user.is_authenticated:
        location_history = get_location_history(user)
        favorite_locations = get_favorite_locations(user)
    return render(
        request,
        'weather_app/dashboard.html', {
            'location': location,
            'weather': weather,
            'air_pollution': air_pollution,
            'charts': charts,
            'location_history': get_location_history(user),
            'favorite_locations': get_favorite_locations(user)})
