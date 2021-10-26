from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from weather_app.models import Location
from django.db import IntegrityError
from django.contrib.auth import login, authenticate
from urllib.parse import urlencode
from django.urls import reverse
import pprint


def user_profile(request):
    def get_location_query(request):
        # TODO Move to utils.py
        if request.method == 'GET':
            latitude = request.GET.get('latitude')
            longitude = request.GET.get('longitude')
            label = request.GET.get('label')
        elif request.method == 'POST':
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            label = request.POST.get('label')
        if latitude and longitude and label:
            return {
                'latitude': latitude,
                'longitude': longitude,
                'label': label}
        else:
            return {}

    def redirect_to_dashboard(location):
        # TODO Move to utils.py
        base_url = reverse('dashboard')
        params = urlencode(location)
        uri = f'{base_url}?{params}'
        return redirect(uri)

    try:
        if request.method == 'GET':
            return render(
                request,
                'weather_app/user_profile.html', {
                    'location': get_location_query(request)})
        elif request.method == 'POST':
            user = authenticate(
                username=request.POST.get('username'),
                password=request.POST.get('password'))
            if not user:
                return render(
                    request,
                    'weather_app/user_profile.html', {
                        'alert': 'Username and password do not match.',
                        'location': get_location_query(request)})
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            clear_history = request.POST.get('clear_history')
            preserve_favorites = request.POST.get('preserve_favorites')
            delete_account = request.POST.get('delete_account')
            i_am_sure = request.POST.get('i_am_sure')
            if new_password1 or new_password2:
                # Change password
                if password != new_password1 == new_password2:
                    user.set_password(new_password1)
                    user.save()
                    login(request, user)
                    return redirect_to_dashboard(get_location_query(request)) # Success
                elif password == new_password1 == new_password2:
                    return render(
                        request,
                        'weather_app/user_profile.html', {
                            'alert': 'New password must be different from the old one.',
                            'location': get_location_query(request)})
                elif new_password1 != new_password2:
                    return render(
                        request,
                        'weather_app/user_profile.html', {
                            'alert': 'New passwords do not match.',
                            'location': get_location_query(request)})
            elif clear_history:
                # Clear history
                if preserve_favorites:
                    Location.objects.filter(
                        user=user,
                        is_favorite=False).delete()
                else:
                    Location.objects.filter(
                        user=user).delete()
                return redirect_to_dashboard(get_location_query(request))
            elif delete_account and i_am_sure:
                user.delete()
                return redirect_to_dashboard(get_location_query(request))
            else:
                return render(
                    request,
                    'weather_app/user_profile.html', {
                        'alert': 'Invalid options.',
                        'location': get_location_query(request)})
    except Exception as err:
        messages.error(
            request, {
                'header': 'Internal error',
                'description': 'Processing user profile options failed.',
                'icon': 'fas fa-times-circle',
                'admin_details': [
                    'Method: user_profile(request)',
                    f'Exception: {pprint.pformat(err)}']})
        return render(request, 'weather_app/dashboard.html')