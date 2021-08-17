from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
import requests
import pprint
import json

found_locations = None
selected_location = None

def weather_dashboard(request):
    global selected_location

    def convert_timestamps_to_datetime(weather):
        weather['current']['dt'] = datetime.fromtimestamp(weather['current']['dt'])
        weather['current']['sunrise'] = datetime.fromtimestamp(weather['current']['sunrise'])
        weather['current']['sunset'] = datetime.fromtimestamp(weather['current']['sunset'])
        for minute in range(len(weather['minutely'])):
            weather['minutely'][minute]['dt'] = datetime.fromtimestamp(weather['minutely'][minute]['dt'])
        return weather

    if selected_location:
        lat = selected_location['geometry']['coordinates'][1]
        lon = selected_location['geometry']['coordinates'][0]
        weather_query = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid=6fe37effcfa866ecec5fd235699a402d&units=metric'
        weather = requests.get(weather_query)
        weather = weather.json()
        weather = convert_timestamps_to_datetime(weather)
        chart_data = {
            'minutely': {
                'dt': [],
                'precipitation': [],
            }
        }

        for minute in weather['minutely']:
            chart_data['minutely']['dt'].append(minute['dt'].strftime("%H:%M"))
            chart_data['minutely']['precipitation'].append(minute['precipitation'])

        headline = 'Weather Dashboard'
        return render(request, 'weather_app/weather_dashboard.html',
            {'selected_location': selected_location, 'weather': weather, 'headline': headline, 'chart_data': chart_data})
    else:
        headline = 'Please search location...'
        return render(request, 'weather_app/no_location.html', {'headline': headline})

def search_results(request):
    global found_locations
    search_text = request.GET.get('search_text')
    found_locations = requests.get(
        'https://api.openrouteservice.org/geocode/search?api_key=5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71&size=50&text=' + search_text)
    found_locations = found_locations.json()['features']
    if found_locations:
        headline = 'Select location'
        return render(request, 'weather_app/search_results.html', {'found_locations': found_locations, 'headline': headline})
    else:
        headline = 'Nothing found...'
        return render(request, 'weather_app/search_results.html', {'found_locations': found_locations, 'headline': headline})
    
def set_location(request):
    global found_locations
    global selected_location
    location_index = int(request.GET.get('location_index')) - 1
    selected_location = found_locations[location_index]
    return redirect('weather_dashboard')