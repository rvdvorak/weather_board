from django.contrib.auth import logout
from weather_app.views.utils import get_location_query, redirect_to_dashboard


def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect_to_dashboard(get_location_query(request))
