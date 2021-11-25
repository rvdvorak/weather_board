from weather_app.models import Location
from weather_app.views.utils import redirect_to_dashboard, redirect_to_login, get_location_params


# TODO Test add favorite location
# TODO Test remove favorite location
# TODO Refactor using location_params
# TODO Implement "login required" decorator
def update_location(request):
    user = request.user
    if not user.is_authenticated:
        redirect_to_login(get_location_params(request))
    location = Location.objects.filter(
        user=user,
        id=int(request.POST.get('location_id')))[0]
    if request.POST.get('is_favorite') == 'yes':
        location.is_favorite = True
    elif request.POST.get('is_favorite') == 'no':
        location.is_favorite = False
    location.save()
    return redirect_to_dashboard({
        'latitude': location.latitude,
        'longitude': location.longitude,
        'label': location.label})
