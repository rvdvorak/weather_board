from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse
from weather_app.models import Location
import pprint


def update_location(request):
    try:
        location = Location.objects.filter(
            user=request.user,
            id=int(request.POST.get('location_id')))[0]
        if request.POST.get('is_favorite') == 'yes':
            location.is_favorite = True
        elif request.POST.get('is_favorite') == 'no':
            location.is_favorite = False
        location.save()
        base_url = reverse('dashboard')
        params = urlencode({
            'latitude': location.latitude,
            'longitude': location.longitude,
            'label': location.label})
        uri = f'{base_url}?{params}'
        return redirect(uri)
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'Location update failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: update_location(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')
