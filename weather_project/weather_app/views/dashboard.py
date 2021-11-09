from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
import pprint
from .utils import *

# TODO Sunrise/Sunset: http://127.0.0.1:8000/?latitude=81.475139&longitude=-161.169992&label=Arctic+Ocean

def dashboard(request):
    user = request.user
    weather = None
    air_pollution = None
    charts = None
    location_history = None
    favorite_locations = None
    location = get_location_instance(get_location_query(request), user)
    if location:
        weather = get_weather(location)
        timezone = pytz.timezone(weather['timezone'])
        air_pollution = get_air_pollution(location, timezone)
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
            'location_history': location_history,
            'favorite_locations': favorite_locations})
