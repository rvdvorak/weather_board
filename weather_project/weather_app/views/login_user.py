from django.template.response import TemplateResponse
from django.contrib.auth import login, authenticate
from weather_app.views.utils import get_location_query, redirect_to_dashboard, get_credentials


def render_login_page(request, error_message=''):
    return TemplateResponse(
        request,
        'weather_app/login_user.html', {
            'query': get_location_query(request),
            'error_message': error_message})


def login_user(request):
    # Handle the login process
    if request.method == 'GET':
        # Show login page
        return render_login_page(request)
    elif request.method == 'POST':
        # Try to login
        user = authenticate(request, **get_credentials(request))
        if user:
            login(request, user)
            return redirect_to_dashboard(get_location_query(request))
            # Login successful
        else:
            # Login failed
            return render_login_page(
                request,
                error_message='Username and password do not match.')
