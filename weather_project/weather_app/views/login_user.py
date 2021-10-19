from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth import login
from urllib.parse import urlencode
from django.urls import reverse
import pprint


def login_user(request):
    try:
        location = {
            'latitude': '',
            'longitude': '',
            'label': ''}
        if request.method == 'GET':
            latitude = request.GET.get('latitude')
            longitude = request.GET.get('longitude')
            label = request.GET.get('label')
            if latitude and longitude and label:
                location['latitude'] = latitude
                location['longitude'] = longitude
                location['label'] = label
            return render(
                request,
                'weather_app/login_user.html', {
                    'location': location})
        elif request.method == 'POST':
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            label = request.POST.get('label')
            if latitude and longitude and label:
                location['latitude'] = latitude
                location['longitude'] = longitude
                location['label'] = label
            user = authenticate(
                request,
                username=request.POST['username'],
                password=request.POST['password'])
            if user:
                login(request, user)
                base_url = reverse('dashboard')
                params = urlencode(location)
                uri = f'{base_url}?{params}'
                return redirect(uri)
            else:
                return render(
                    request,
                    'weather_app/login_user.html', {
                        'alert': 'Username and password do not match.',
                        'location': location})
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'Log-in failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: login_user(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')
