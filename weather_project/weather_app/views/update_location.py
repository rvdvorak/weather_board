from weather_app.models import Location
from weather_app.views.utils import redirect_to_dashboard


# TODO Tests
def update_location(request):
    location = Location.objects.filter(
        user=request.user,
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
