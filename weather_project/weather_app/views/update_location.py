from weather_app.models import Location
from weather_app.views.utils import get_query, redirect_to_dashboard
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from pprint import pprint


@login_required(redirect_field_name='next_url')
def update_location(request):
    # Currently updates only the "is_favorite" attribute.
    location_id = request.POST.get('location_id')  # String
    is_favorite = request.POST.get('is_favorite')  # String
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
    return redirect_to_dashboard(get_query(request))
