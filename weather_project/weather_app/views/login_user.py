from django.template.response import TemplateResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from weather_app.views.utils import get_query, redirect_to_dashboard
from django.shortcuts import redirect
from urllib.parse import urlencode

# TODO def render_login_page(reguest, error_message=''):


def login_user(request):
    query = get_query(request)
    if request.method == 'GET':
        # Show login page
        next_url = request.GET.get('next_url') or ''
        return TemplateResponse(
            request,
            'weather_app/login_user.html', {
                'next_url': next_url,
                'query': query})
    elif request.method == 'POST':
        # Try to login
        next_url = request.POST.get('next_url') or ''
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if next_url:
                return redirect(f"{next_url}?{urlencode(query)}")
            else:
                return redirect_to_dashboard(query)
        else:
            # Login failed
            return TemplateResponse(
                request,
                'weather_app/login_user.html', {
                    'error_message': 'Username and password do not match.',
                    'display_mode': query['display_mode'],
                    'location': {
                        'label': query['label'],
                        'latitude': query['latitude'],
                        'longitude': query['longitude']},
                    'next_url': next_url})
