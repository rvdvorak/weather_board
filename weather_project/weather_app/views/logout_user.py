from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from urllib.parse import urlencode
from django.urls import reverse
import pprint

#TODO Styles

def logout_user(request):
    try:
        location = {
            'latitude': '',
            'longitude': '',
            'label': ''}
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        label = request.GET.get('label')
        if latitude and longitude and label:
            location['latitude'] = latitude
            location['longitude'] = longitude
            location['label'] = label
        if request.user.is_authenticated:
            logout(request)
        base_url = reverse('dashboard')
        params = urlencode(location)
        uri = f'{base_url}?{params}'
        return redirect(uri)
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'Log-out failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: logout_user(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/message.html')
        