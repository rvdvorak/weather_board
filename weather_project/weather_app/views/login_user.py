from django.template.response import TemplateResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from weather_app.views.utils import get_location_params, redirect_to_dashboard


def login_user(request):
    location_params = get_location_params(request)
    if request.method == 'GET':
        return TemplateResponse(
            request,
            'weather_app/login_user.html', {
                'location_params': location_params})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect_to_dashboard(location_params)
        else:
            return TemplateResponse(
                request,
                'weather_app/login_user.html', {
                    'error_message': 'Username and password do not match.',
                    'location_params': location_params})
