from weather_app.models import Location
from weather_app.views.utils import redirect_to_dashboard, get_location_params, get_view_mode
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from pprint import pprint


@login_required(redirect_field_name='next_url')
def update_location(request):
    location_id = request.POST.get('location_id')
    is_favorite = request.POST.get('is_favorite')
    if location_id and is_favorite:  # Both are strings if they are present.
        match = Location.objects.filter(
            pk=location_id,
            user=request.user)
        if match:
            location = match[0]
            location.is_favorite = is_favorite
            location.save()
    return redirect_to_dashboard(
        get_location_params(request),
        get_view_mode(request))
