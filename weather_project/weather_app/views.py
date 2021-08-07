from django.shortcuts import render
import requests
import datetime


def home(request):
    return render(request, 'weather_app/home.html')

def current(request):
    response = requests.get('https://api.openweathermap.org/data/2.5/onecall?lat=49.2075&lon=16.6861&exclude=minutely,hourly,daily,alerts&appid=6fe37effcfa866ecec5fd235699a402d&units=metric')
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