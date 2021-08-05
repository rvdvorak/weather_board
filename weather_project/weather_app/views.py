from django.shortcuts import render

def home(request):
    return render(request, 'weather_app/home.html')

def current(request):
    return render(request, 'weather_app/current.html')

def forecast(request):
    return render(request, 'weather_app/forecast.html')

def history(request):
    return render(request, 'weather_app/history.html')

def saved(request):
    return render(request, 'weather_app/saved.html')
