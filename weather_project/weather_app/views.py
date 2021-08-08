from django.shortcuts import render
from django.http import HttpResponse
import requests
import datetime
import pprint


def home(request):
    return render(request, 'weather_app/home.html')

def current(request):
    response = requests.get(
        'https://api.openweathermap.org/data/2.5/onecall?lat=49.2075&lon=16.6861&exclude=minutely,hourly,daily,alerts&appid=6fe37effcfa866ecec5fd235699a402d&units=metric')
    weather = response.json()
    ts = int(weather['current']['dt'])
    dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    sunrise_ts = int(weather['current']['sunrise'])
    sunrise = datetime.datetime.fromtimestamp(sunrise_ts).strftime('%Y-%m-%d %H:%M:%S')
    sunset_ts = int(weather['current']['sunset'])
    sunset = datetime.datetime.fromtimestamp(sunset_ts).strftime('%Y-%m-%d %H:%M:%S')

    return render(request, 'weather_app/current.html', {'weather': weather,'dt': dt, 'sunrise': sunrise, 'sunset': sunset})

def forecast(request):
    return render(request, 'weather_app/forecast.html')

def history(request):
    return render(request, 'weather_app/history.html')

def saved(request):
    return render(request, 'weather_app/saved.html')

def locations(request):
    search_location = request.GET.get('search_location')
    response = requests.get(
        'https://api.openrouteservice.org/geocode/search?api_key=5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71&size=50&layers=locality&text=' + search_location)
    found_locations = response.json()['features']
    return render(request, 'weather_app/locations.html', {'found_locations': found_locations})