from django.contrib.auth import logout
from weather_app.views.utils import redirect_to_dashboard, get_location_params


# TODO Tests
def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect_to_dashboard(get_location_params(request))
