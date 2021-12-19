from weather_app.models import Location
from weather_app.views.utils import get_location_query, redirect_to_login, redirect_to_dashboard
from pprint import pprint


def update_location(request):
    # Update the location record in DB.
    # Currently updates only the "is_favorite" attribute.
    if not request.user.is_authenticated:
        return redirect_to_login(get_location_query(request))
    location_id = request.POST.get('location_id')  # type string
    is_favorite = request.POST.get('is_favorite')  # type string
    if location_id and is_favorite:
        match = Location.objects.filter(
            pk=location_id,
            user=request.user)
        if match:
            # Update the location
            location = match[0]
            location.is_favorite = is_favorite
            location.save()
    # Go back to dashboard
    return redirect_to_dashboard(get_location_query(request))
