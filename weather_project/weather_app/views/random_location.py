from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from requests.exceptions import Timeout, HTTPError
import json
import pprint
import random
from .utils import redirect_to_dashboard, get_favorite_locations, get_location_history, get_random_location_params, render_empty_dashboard


def random_location(request):
    user = request.user
    try:
        location_params = get_random_location_params()
    except Timeout as err:
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again later...',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': [
                    f'Exception: {pprint.pformat(err)}']})
        return render_empty_dashboard(request)
    except HTTPError as err:
        messages.error(
            request, {
                'header': 'Location service error',
                'description': 'Communication with location service failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': [
                    f'Exception: {pprint.pformat(err)}']})
        return render_empty_dashboard(request)
    return redirect_to_dashboard(location_params)
