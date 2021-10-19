from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from urllib.parse import urlencode
from django.urls import reverse

import pprint

#TODO Styles

def register_user(request):
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
                'weather_app/register_user.html', {
                    'location': location})
        elif request.method == 'POST':
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            label = request.POST.get('label')
            if latitude and longitude and label:
                location['latitude'] = latitude
                location['longitude'] = longitude
                location['label'] = label
            if request.POST['password1'] == request.POST['password2']:
                try:
                    user = User.objects.create_user(request.POST['username'], password=request.POST['password1'])
                    user.save()
                    login(request, user)
                    base_url = reverse('dashboard')
                    params = urlencode(location)
                    uri = f'{base_url}?{params}'
                    return redirect(uri)
                except IntegrityError:
                    return render(
                        request,
                        'weather_app/register_user.html', {
                            'alert': 'User already exists. Please choose different username.',
                            'location': location})
            else:
                return render(
                    request,
                    'weather_app/register_user.html', {
                        'alert': 'Passwords do not match.',
                        'location': location})
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'User registration failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: register_user(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')