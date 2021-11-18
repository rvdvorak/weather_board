from requests.exceptions import Timeout, HTTPError
from django.contrib import messages
import pprint
from weather_app.views.utils import redirect_to_dashboard, get_favorite_locations, get_location_history, get_random_location_params, render_dashboard
from weather_app.views.API_keys import ORS_key


# TODO Tests
def random_location(request):
    user = request.user
    try:
        location_params = get_random_location_params(ORS_key)
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Location service error',
                'description': 'Communication with location service failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': f'Exception: {pprint.pformat(err)}'})
        return render_dashboard(request)
    return redirect_to_dashboard(location_params)
