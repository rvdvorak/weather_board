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
        weather['current']['dt'] = datetime.fromtimestamp(
            weather['current']['dt'])
        weather['current']['sunrise'] = datetime.fromtimestamp(
            weather['current']['sunrise'])
        weather['current']['sunset'] = datetime.fromtimestamp(
            weather['current']['sunset'])
        for minute in range(len(weather['minutely'])):
            weather['minutely'][minute]['dt'] = datetime.fromtimestamp(
                weather['minutely'][minute]['dt'])
        return weather

    if not selected_location:
        message = {
            'style': 'lightblue',
            'header': 'Hint',
            'content': 'Search the location to show the weather.',
        }
        return render(request, 'weather_app/weather_dashboard.html', {'message': message})

    lat = selected_location['geometry']['coordinates'][1]
    lon = selected_location['geometry']['coordinates'][0]
    weather_query = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid=6fe37effcfa866ecec5fd235699a402d&units=metric'
    weather_response = requests.get(weather_query)

    if not weather_response.status_code == 200:
        message = {
            'style': 'danger',
            'header': 'Weather data error',
            'content': f'Request for weather data failed. Please try again later. (Weather server status: {weather_response.status_code})'
        }
        return render(request, 'weather_app/weather_dashboard.html', {'message': message})

    weather = weather_response.json()
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

    return render(request, 'weather_app/weather_dashboard.html',
                  {'selected_location': selected_location, 'weather': weather, 'chart_data': chart_data})


def search_results(request):
    global found_locations

    found_locations = None
    search_text = request.GET.get('search_text')

    if not search_text:
        message = {
            'style': 'lightblue',
            'header': 'Hint',
            'content': 'First enter the name of the location you want to search.',
        }
        return render(request, 'weather_app/search_results.html', {'message': message})

    location_query = 'https://api.openrouteservice.org/geocode/search?api_key=5b3ce3597851110001cf624830716a6e069742efa48b8fffc0f8fe71&size=50&text=' + search_text
    location_response = requests.get(location_query)

    if not location_response.status_code == 200:
        message = {
            'style': 'danger',
            'header': 'Search location error',
            'content': f'Search request failed. Please try again later. (Location server status: {openrouteservice_response.status_code})',
        }
        return render(request, 'weather_app/search_results.html', {'message': message})

    found_locations = location_response.json()['features']

    if not found_locations:
        message = {
            'style': 'lightblue',
            'header': 'No location found',
            'content': 'You probably entered the location incorrectly. Please try again.',
        }
        return render(request, 'weather_app/search_results.html', {'message': message})

    return render(request, 'weather_app/search_results.html', {'found_locations': found_locations})


def set_location(request):
    global found_locations
    global selected_location
    location_index = int(request.GET.get('location_index')) - 1
    selected_location = found_locations[location_index]
    return redirect('weather_dashboard')
