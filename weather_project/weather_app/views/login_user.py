from django.template.response import TemplateResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from weather_app.views.utils import get_location_params, redirect_to_dashboard
from django.shortcuts import redirect
from urllib.parse import urlencode


def login_user(request):
    location_params = get_location_params(request)
    if request.method == 'GET':
        # Show login page
        next_url = request.GET.get('next_url')
        return TemplateResponse(
            request,
            'weather_app/login_user.html', {
                'location_params': location_params,
                'next_url': next_url})
    elif request.method == 'POST':
        # Try to login
        next_url = request.POST.get('next_url')
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'))
        if user:
            # Login successful
            login(request, user)
            if next_url:
                return redirect(f"{next_url}?{urlencode(location_params)}")
            else:
                return redirect_to_dashboard(location_params)
        else:
            # Login failed
            return TemplateResponse(
                request,
                'weather_app/login_user.html', {
                    'error_message': 'Username and password do not match.',
                    'location_params': location_params,
                    'next_url': next_url})
