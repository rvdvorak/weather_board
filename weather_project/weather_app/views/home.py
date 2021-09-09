from django.shortcuts import render

def home(request):
    return render(request, 'weather_app/home.html')