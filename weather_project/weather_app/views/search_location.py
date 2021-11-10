from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponse
import requests
from requests.exceptions import Timeout
import json
import pprint
from .utils import get_search_results, get_location_history, get_favorite_locations, redirect_to_dashboard, render_empty_dashboard


def search_location(request):
    user = request.user
    max_count = 20
    search_query = request.GET.get('search_query')
    if search_query == '' or search_query == None:
        # Missing search text
        messages.warning(
            request, {
                'header': 'Nothing to search',
                'description': 'First enter the name of the location to search.',
                'icon': 'bi bi-geo-alt-fill',
                'show_search_form': True})
        return render_empty_dashboard(request)
    try:
        search_results = get_search_results(search_query, max_count=max_count)
    except Timeout as err:
        # API request time out
        messages.warning(
            request, {
                'header': 'Location service time out',
                'description': 'Please try it again or later.',
                'icon': 'fas fa-hourglass-end',
                'show_search_form': True,
                'admin_details': [
                    f'Exception: {pprint.pformat(err)}']})
        return render_empty_dashboard(request)
    except HTTPError as err:
        # API request failed
        messages.error(
            request, {
                'header': 'Location service error',
                'description': 'Communication with location service failed.',
                'icon': 'fas fa-times-circle',
                'show_search_form': True,
                'admin_details': [
                    f'Exception: {pprint.pformat(err)}']})
        return render_empty_dashboard(request)
    if len(search_results) == 0:
        # Location not found
        messages.warning(
            request, {
                'header': 'Location not found',
                'description': f'"{search_query}" is probably incorrect. Please try something else.',
                'icon': 'bi bi-geo-alt-fill',
                'show_search_form': True})
        return render_empty_dashboard(request)
    elif len(search_results) == 1:
        # Single match => rerdirect to Dashboard
        location_params = {
            'latitude': search_results[0]['geometry']['coordinates'][1],
            'longitude': search_results[0]['geometry']['coordinates'][0],
            'label': search_results[0]['properties']['label']}
        return redirect_to_dashboard(location_params)
    elif len(search_results) > 1:
        # Multiple matches => show search results as message
        if len(search_results) == max_count:
            # Too many matches
            message_description = f'Showing only first {max_count} matching locations:'
        else:
            message_description = None
        messages.success(
            request, {
                'header': 'Select location',
                'description': message_description,
                'icon': 'bi bi-geo-alt-fill',
                'search_results': search_results,
                'show_search_form': True})
        return render_empty_dashboard(request)
