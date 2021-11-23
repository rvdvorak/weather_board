from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login
from weather_app.views.utils import redirect_to_dashboard, get_location_params


# TODO Tests
def register_user(request):
    if request.method == 'GET':
        return TemplateResponse(
            request,
            'weather_app/register_user.html', {
                'location_params': get_location_params(request)})
    elif request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 == password2:
            user = User.objects.create_user(username, password=password1)
            try:
                user.save()
            except IntegrityError:
                return TemplateResponse(
                    request,
                    'weather_app/register_user.html', {
                        'error_message': 'User already exists. Please choose different username.',
                        'location_params': get_location_params(request)})
                login(request, user)
                return redirect_to_dashboard(get_location_params(request))
        else:
            return TemplateResponse(
                request,
                'weather_app/register_user.html', {
                    'error_message': 'Passwords do not match.',
                    'location_params': get_location_params(request)})
