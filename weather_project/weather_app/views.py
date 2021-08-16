from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
import requests
import pprint
import json

found_locations = None
selected_location = None

def weather(request):
    global selected_location
    if selected_location:
        lat = selected_location['geometry']['coordinates'][1]
        lon = selected_location['geometry']['coordinates'][0]
        weather_query = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid=6fe37effcfa866ecec5fd235699a402d&units=metric'
        weather_response = requests.get(weather_query)
        weather = weather_response.json()
        weather['current']['dt'] = datetime.fromtimestamp(weather['current']['dt'])
        weather['current']['sunrise'] = datetime.fromtimestamp(weather['current']['sunrise'])
        weather['current']['sunset'] = datetime.fromtimestamp(weather['current']['sunset'])
        return render(request, 'weather_app/weather.html', {'location': selected_location, 'weather': weather})
    else:
        return render(request, 'weather_app/no_location.html')

def search_results(request):
    global found_locations
    search_text = request.GET.get('search_text')
    locations_response = requests.get(
        'https://api.openrouteservice.org/geocode/search?api_key=5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71&size=50&text=' + search_text)
    found_locations = locations_response.json()['features']
    return render(request, 'weather_app/search_results.html', {'found_locations': found_locations})
    
def set_location(request):
    global found_locations
    global selected_location
    location_index = int(request.GET.get('location_index')) - 1
    selected_location = found_locations[location_index]
    return redirect('weather')