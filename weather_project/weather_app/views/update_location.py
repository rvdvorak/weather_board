from weather_app.models import Location
from weather_app.views.utils import redirect_to_dashboard, redirect_to_login, get_location_params


# TODO Implement "login required" decorator
def update_location(request):
    user = request.user
    location_id = request.POST.get('location_id')
    is_favorite = request.POST.get('is_favorite')
    location_params = get_location_params(request)
    if location_id and user.is_authenticated:
        location = Location.objects.filter(
            pk=location_id,
            user=user)[0]
        location.is_favorite = is_favorite
        location.save()
    return redirect_to_dashboard(location_params)
