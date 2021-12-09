from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login
from weather_app.views.utils import get_location_query

# TODO Password validation


def render_registration_page(request, error_message='', success_message=''):
    query = get_location_query(request)
    return TemplateResponse(
        request,
        'weather_app/register_user.html', {
            'query': query,
            'error_message': error_message,
            'success_message': success_message})


def register_user(request):
    if request.method == 'GET':
        # Show registration page
        return render_registration_page(request)
    if request.method == 'POST':
        # Try to register new user
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if not password1 == password2:
            # Passwords do not match
            return render_registration_page(request, 'Passwords do not match.')
        try:
            user = User.objects.create_user(username, password=password1)
            user.save()
        except IntegrityError:
            # Username already exists
            return render_registration_page(
                request,
                'User already exists. Please choose different username.')
        login(request, user)
        # Registration successful
        return render_registration_page(
            request,
            success_message='Your account has been created successfully.')
