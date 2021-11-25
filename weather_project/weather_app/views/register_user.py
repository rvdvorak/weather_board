from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login
from weather_app.views.utils import redirect_to_dashboard, get_location_params, get_location_history, get_favorite_locations


def render_registration_page(request, error_message=None):
    return TemplateResponse(
        request,
        'weather_app/register_user.html', {
            'error_message': error_message,
            'location_params': get_location_params(request),
            'location_history': get_location_history(request.user),
            'favorite_locations': get_favorite_locations(request.user)})


def register_user(request):
    # TODO Password validation
    if request.method == 'GET':
        # TODO Test show user registration page
        return render_registration_page(request)
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if not password1 == password2:
            # TODO Test register user with unmatched passwords
            return render_registration_page(request, 'Passwords do not match.')
        try:
            user = User.objects.create_user(username, password=password1)
            user.save()
        except IntegrityError:
            # TODO Test register existing user
            return render_registration_page(
                request,
                'User already exists. Please choose different username.')
        login(request, user)
        # Registration successful
        # TODO Test register new user
        # TODO Success notification
        return redirect_to_dashboard(get_location_params(request))
