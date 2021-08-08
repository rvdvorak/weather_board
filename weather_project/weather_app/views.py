from django.shortcuts import render
from django.http import HttpResponse
import requests
import datetime
import pprint
import json

found_locations = None
selected_location = None

def home(request):
    return render(request, 'weather_app/home.html')

def current(request):
    location_index = int(request.GET.get('location_index')) - 1
    selected_location = found_locations[location_index]
    lat = selected_location['geometry']['coordinates'][1]
    lon = selected_location['geometry']['coordinates'][0]


    weather_response = requests.get(
        f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid=6fe37effcfa866ecec5fd235699a402d&units=metric')
    weather = weather_response.json()
    ts = int(weather['current']['dt'])
    dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    sunrise_ts = int(weather['current']['sunrise'])
    sunrise = datetime.datetime.fromtimestamp(sunrise_ts).strftime('%Y-%m-%d %H:%M:%S')
    sunset_ts = int(weather['current']['sunset'])
    sunset = datetime.datetime.fromtimestamp(sunset_ts).strftime('%Y-%m-%d %H:%M:%S')

    return render(request, 'weather_app/current.html', {'location': selected_location, 'weather': weather,'dt': dt, 'sunrise': sunrise, 'sunset': sunset})

def forecast(request):
    return render(request, 'weather_app/forecast.html')

def history(request):
    return render(request, 'weather_app/history.html')

def saved(request):
    return render(request, 'weather_app/saved.html')

def locations(request):
    search_text = request.GET.get('search_text')
    locations_response = requests.get(
        'https://api.openrouteservice.org/geocode/search?api_key=5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71&size=50&text=' + search_text)
    global found_locations
    found_locations = locations_response.json()['features']
    return render(request, 'weather_app/locations.html', {'found_locations': found_locations})
    