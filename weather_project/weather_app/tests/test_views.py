from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import login, authenticate
from django.contrib import auth
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from urllib.parse import urlencode, urlparse, parse_qs, quote_plus
from requests.exceptions import Timeout, HTTPError
from django.db.models.query import QuerySet
from weather_app.views import *
from weather_app.models import User, Location
from weather_app.tests.utils import *
from datetime import datetime
from django.conf import settings
import pprint
import pytz
import copy

# TODO Implement fixtures


class TestDashboard(TestCase):
    # Weather API docs:
    # https://openweathermap.org/api/one-call-api#parameter

    # Air pollution API docs:
    # https://openweathermap.org/api/air-pollution#fields

    def test_dashboard_with_query_with_login(self):
        user_data = setup_test_user_data()
        client = Client()
        client.login(**user_data['credentials'])
        url = reverse('dashboard')
        query = get_test_query()
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/dashboard.html')
        assert len(list(response.context['messages'])) == 0
        check_template_context_with_query(response.context, query)
        check_template_context_with_user_data(response.context, user_data)

    def test_dashboard_with_no_query_with_login(self):
        user_data = setup_test_user_data()
        client = Client()
        client.login(**user_data['credentials'])
        url = reverse('dashboard')
        response = client.get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/search_location.html')
        assert len(list(response.context['messages'])) == 0
        check_template_context_with_no_query(response.context)
        check_template_context_with_user_data(response.context, user_data)

    def test_dashboard_with_query_with_no_login(self):
        url = reverse('dashboard')
        query = get_test_query()
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/dashboard.html')
        assert len(list(response.context['messages'])) == 0
        check_template_context_with_query(response.context, query)
        check_template_context_with_no_user_data(response.context)

    def test_dashboard_with_no_query_with_no_login(self):
        response = Client().get(reverse('dashboard'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/search_location.html')
        assert len(list(response.context['messages'])) == 0
        check_template_context_with_no_query(response.context)
        check_template_context_with_no_user_data(response.context)

    def test_dashboard_with_weather_API_timeout_with_login(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_query()
        request, messages = get_get_request_and_messages(
            url, query, user_data['user'])
        response = dashboard(request, weather_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Weather service time out')
        check_template_context_with_error_message(response.context_data, query)
        check_template_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_weather_API_http_error_with_login(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_query()
        request, messages = get_get_request_and_messages(
            url, query, user_data['user'])
        response = dashboard(request, weather_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Weather service error')
        check_template_context_with_error_message(response.context_data, query)
        check_template_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_air_pollution_API_timeout_with_login(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_query()
        request, messages = get_get_request_and_messages(
            url, query, user_data['user'])
        response = dashboard(request, air_pltn_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Air pollution service time out')
        check_template_context_with_error_message(response.context_data, query)
        check_template_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_air_pollution_API_http_error_with_login(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_query()
        request, messages = get_get_request_and_messages(
            url, query, user_data['user'])
        response = dashboard(request, air_pltn_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Air pollution service error')
        check_template_context_with_error_message(response.context_data, query)
        check_template_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_incorrect_query_with_login(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_query()
        query['latitude'] = '91' # Out of range
        client = Client()
        client.login(**user_data['credentials'])
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        messages = list(response.context['messages'])
        assert len(messages) == 1
        self.assertEquals(
            messages[0].message['header'],
            'Incorrect location parameters')
        check_template_context_with_error_message(response.context, query)
        check_template_context_with_user_data(response.context, user_data)

    def test_convert_timestamps_to_datetimes(self):
        # TODO Test timestamps just before/after DST begin/end
        utc_timestamp = 1636339065
        timezone = pytz.timezone('Europe/Prague')
        local_datetime = datetime.fromtimestamp(utc_timestamp, timezone)
        keys_to_convert = ['dt', 'sunrise', 'sunset']
        input_data = {
            'abc': 123456789,
            'jkl': [{
                    'dt': utc_timestamp,
                    'xyz': 987654321,
                    'sunrise': utc_timestamp
                    }, {
                    'sunset': utc_timestamp,
                    'def': 123123123,
                    'x': [{
                        'dt': utc_timestamp,
                        'asd': 99999999999,
                        'q': {
                            'w': 888888888,
                            'dt': utc_timestamp,
                            'sunrise': utc_timestamp,
                            'sunset': utc_timestamp}}]}]}
        output_data = {
            'abc': 123456789,
            'jkl': [{
                    'dt': local_datetime,
                    'xyz': 987654321,
                    'sunrise': local_datetime
                    }, {
                    'sunset': local_datetime,
                    'def': 123123123,
                    'x': [{
                        'dt': local_datetime,
                        'asd': 99999999999,
                        'q': {
                            'w': 888888888,
                            'dt': local_datetime,
                            'sunrise': local_datetime,
                            'sunset': local_datetime}}]}]}
        assert convert_timestamps_to_datetimes(
            copy.deepcopy(input_data),
            keys_to_convert,
            timezone) == output_data
        assert convert_timestamps_to_datetimes(
            copy.deepcopy([[[input_data]]]),
            keys_to_convert,
            timezone) == [[[output_data]]]

    def test_get_charts(self):
        weather = sample_weather()
        air_pollution = sample_air_pollution()
        charts = sample_charts()
        assert get_charts(weather, air_pollution) == charts


class TestSearchLocation(TestCase):
    # Location API docs:
    # https://openrouteservice.org/dev/#/api-docs/geocode/search/get

    def test_search_location_with_too_many_matches_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Set up request
        url = reverse('search_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Lhota'}
        lhota = {
            'label': 'Lhota, OK, Czechia',
            'latitude': 49.71667,
            'longitude': 17.28333}
        # Set up test client
        client = Client()
        client.login(**credentials)
        # Send request
        response = client.get(url, query)
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        # Search results as a message
        assert len(list(response.context['messages'])) == 1
        message = list(response.context['messages'])[0].message
        self.assertEquals(
            message['header'],
            'Select location')
        self.assertEquals(
            message['description'],
            'Showing only first 20 matching locations:')
        assert lhota in message['search_results']
        assert len(message['search_results']) == 20
        # Query
        assert response.context['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context['location'] == None
        assert response.context['weather'] == None
        assert response.context['air_pollution'] == None
        assert response.context['charts'] == None
        # User (private) data
        assert favorite_location in response.context['location_history']
        assert ordinary_location in response.context['location_history']
        assert favorite_location in response.context['favorite_locations']
        assert not ordinary_location in response.context['favorite_locations']

    def test_search_location_with_multiple_matches_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Set up request
        url = reverse('search_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Praha'}
        praha = {
            'label': 'Prague, Czechia',
            'latitude': 50.06694,
            'longitude': 14.460249}
        # Set up test client
        client = Client()
        client.login(**credentials)
        # Send request
        response = client.get(url, query)
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        # Search results as a message
        assert len(list(response.context['messages'])) == 1
        message = list(response.context['messages'])[0].message
        self.assertEquals(
            message['header'],
            'Select location')
        self.assertEquals(
            message['description'],
            None)
        assert praha in message['search_results']
        assert len(message['search_results']) > 3
        # Query
        assert response.context['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context['location'] == None
        assert response.context['weather'] == None
        assert response.context['air_pollution'] == None
        assert response.context['charts'] == None
        # User (private) data
        assert favorite_location in response.context['location_history']
        assert ordinary_location in response.context['location_history']
        assert favorite_location in response.context['favorite_locations']
        assert not ordinary_location in response.context['favorite_locations']

    def test_search_location_with_single_match_with_no_login(self):
        # Set up request
        url = reverse('search_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Růžďka'}
        # Send request
        response = Client().get(url, query)
        # Test response
        redirect_query = {
            'display_mode': get_display_modes()[1],
            'label': 'Růžďka, ZK, Czechia',
            'latitude': 49.39395,
            'longitude': 17.99559}
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)

    def test_search_location_without_match_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Set up request
        url = reverse('search_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'incorrect_location_name'}
        # Set up test client
        client = Client()
        client.login(**credentials)
        # Send request
        response = client.get(url, query)
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        # Search results as a message
        assert len(list(response.context['messages'])) == 1
        message = list(response.context['messages'])[0].message
        self.assertEquals(
            message['header'],
            'Location not found')
        assert message['search_results'] == None
        # Query
        assert response.context['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context['location'] == None
        assert response.context['weather'] == None
        assert response.context['air_pollution'] == None
        assert response.context['charts'] == None
        # User (private) data
        assert favorite_location in response.context['location_history']
        assert ordinary_location in response.context['location_history']
        assert favorite_location in response.context['favorite_locations']
        assert not ordinary_location in response.context['favorite_locations']

    def test_search_location_with_no_query_with_no_login(self):
        # Send request
        response = Client().get(reverse('search_location'))
        # Test response
        redirect_query = {
            'display_mode': get_display_modes()[0],
            'label': '',
            'latitude': '',
            'longitude': ''}
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)

    def test_search_location_with_API_timeout_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Setup request
        base_url = reverse('search_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Brno'}
        uri = f'{base_url}?{urlencode(query)}'
        request = RequestFactory().get(uri)
        request.user = user
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Send request
        response = search_location(request, ORS_timeout=0.00001)
        # Test response
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service time out')
        # Query
        assert response.context_data['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context_data['location'] == None
        assert response.context_data['weather'] == None
        assert response.context_data['air_pollution'] == None
        assert response.context_data['charts'] == None
        # User (private) data
        assert favorite_location in response.context_data['location_history']
        assert ordinary_location in response.context_data['location_history']
        assert favorite_location in response.context_data['favorite_locations']
        assert not ordinary_location in response.context_data['favorite_locations']

    def test_search_location_with_API_http_error_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Setup request
        base_url = reverse('search_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Brno'}
        uri = f'{base_url}?{urlencode(query)}'
        request = RequestFactory().get(uri)
        request.user = user
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Send request
        response = search_location(request, ORS_key='bad_key')
        # Test response
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service error')
        # Query
        assert response.context_data['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context_data['location'] == None
        assert response.context_data['weather'] == None
        assert response.context_data['air_pollution'] == None
        assert response.context_data['charts'] == None
        # User (private) data
        assert favorite_location in response.context_data['location_history']
        assert ordinary_location in response.context_data['location_history']
        assert favorite_location in response.context_data['favorite_locations']
        assert not ordinary_location in response.context_data['favorite_locations']


class TestRandomLocation(TestCase):
    # Location API docs:
    # https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get

    def test_show_random_location_with_no_login(self):
        # Set up request
        url = reverse('random_location')
        query = {'display_mode': get_display_modes()[1]}
        # Send request
        response = Client().get(url, query)
        # Test response
        assert response.status_code == 302
        redirect_uri = urlparse(response.url)
        assert redirect_uri.path == reverse('dashboard')
        redirect_query = parse_qs(redirect_uri.query)
        location_label = redirect_query['label'][0]
        assert not location_label in ['', None]
        location_latitude = float(redirect_query['latitude'][0])
        assert -90.0 <= location_latitude <= 90.0
        location_longitude = float(redirect_query['longitude'][0])
        assert -180.0 <= location_longitude <= 180.0
        assert redirect_query['display_mode'][0] == query['display_mode']

    def test_show_random_location_with_API_timeout_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Setup request
        base_url = reverse('random_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Brno'}
        uri = f'{base_url}?{urlencode(query)}'
        request = RequestFactory().get(uri)
        request.user = user
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Send request
        response = search_location(request, ORS_timeout=0.00001)
        # Test response
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service time out')
        # Query
        assert response.context_data['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context_data['location'] == None
        assert response.context_data['weather'] == None
        assert response.context_data['air_pollution'] == None
        assert response.context_data['charts'] == None
        # User (private) data
        assert favorite_location in response.context_data['location_history']
        assert ordinary_location in response.context_data['location_history']
        assert favorite_location in response.context_data['favorite_locations']
        assert not ordinary_location in response.context_data['favorite_locations']

    def test_show_random_location_with_API_http_error_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        ordinary_location = Location(
            **sample_location_params_2(),
            is_favorite=False,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            **sample_location_params_3(),
            is_favorite=True,
            user=user)
        favorite_location.save()
        # Setup request
        base_url = reverse('random_location')
        query = {
            'display_mode': get_display_modes()[1],
            'search_text': 'Brno'}
        uri = f'{base_url}?{urlencode(query)}'
        request = RequestFactory().get(uri)
        request.user = user
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Send request
        response = search_location(request, ORS_key='bad_key')
        # Test response
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service error')
        # Query
        assert response.context_data['query'] == {
            'display_mode': query['display_mode'],
            'label': '',
            'latitude': '',
            'longitude': ''}
        # No dashboard (public) data
        assert response.context_data['location'] == None
        assert response.context_data['weather'] == None
        assert response.context_data['air_pollution'] == None
        assert response.context_data['charts'] == None
        # User (private) data
        assert favorite_location in response.context_data['location_history']
        assert ordinary_location in response.context_data['location_history']
        assert favorite_location in response.context_data['favorite_locations']
        assert not ordinary_location in response.context_data['favorite_locations']


class TestUpdateLocation(TestCase):

    def test_add_favorite_location_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location_params = sample_location_params_1()
        location = Location(
            **location_params,
            is_favorite=False,
            user=user)
        location.save()
        # Set up test client
        client = Client()
        client.login(**credentials)
        # Set up request
        url = reverse('update_location')
        query = {
            'display_mode': get_display_modes()[1],
            **location_params,
            'location_id': location.id,
            'is_favorite': True}  # Add the location to favorites
        # Send request
        response = client.post(url, query)
        # Test response
        redirect_query = {
            'display_mode': query['display_mode'],
            **location_params}
        updated_location = Location.objects.get(pk=location.id)
        assert updated_location.is_favorite  # Location updated successfully
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)

    def test_remove_favorite_location_with_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location_params = sample_location_params_1()
        location = Location(
            **location_params,
            is_favorite=True,
            user=user)
        location.save()
        # Set up test client
        client = Client()
        client.login(**credentials)
        # Set up request
        url = reverse('update_location')
        query = {
            'display_mode': get_display_modes()[1],
            **location_params,
            'location_id': location.id,
            'is_favorite': False}  # Remove the location from favorites
        # Send request
        response = client.post(url, query)
        # Test response
        redirect_query = {
            'display_mode': query['display_mode'],
            **location_params}
        updated_location = Location.objects.get(pk=location.id)
        assert not updated_location.is_favorite  # Location updated successfully
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)

    def test_add_favorite_location_with_no_login(self):
        # Set up user account and user locations
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location_params = sample_location_params_1()
        location = Location(
            **location_params,
            is_favorite=False,
            user=user)
        location.save()
        # Set up test client
        client = Client()
        # Set up request
        url = reverse('update_location')
        query = {
            'display_mode': get_display_modes()[1],
            **location_params,
            'location_id': location.id,
            'is_favorite': True}  # Try to add the location to favorites
        # Send request
        response = client.post(url, query)
        # Test response
        redirect_url = reverse('login_user')
        redirect_query = {
            'display_mode': query['display_mode'],
            **location_params}
        updated_location = Location.objects.get(pk=location.id)
        assert not updated_location.is_favorite  # Location NOT updated
        redirect_uri = f"{redirect_url}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)


class TestRegisterUser(TestCase):

    def test_show_user_registration_page_with_query(self):
        # Set up request
        url = reverse('register_user')
        query = {
            'display_mode': get_display_modes()[1],
            'label': 'Some Location',
            'latitude': '30',
            'longitude': '40'}
        # Send request
        response = Client().get(url, query)
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['query'] == query

    def test_show_user_registration_page_with_no_query(self):
        # Send request
        response = Client().get(reverse('register_user'))
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['query'] == {
            'display_mode': get_display_modes()[0],
            'label': '',
            'latitude': '',
            'longitude': ''}

    def test_register_new_user_with_unmatched_passwords(self):
        # Set up request
        url = reverse('register_user')
        credentials = {
            'username': 'new user',
            'password1': '123456',
            'password2': '123456789'}
        query = {
            'display_mode': get_display_modes()[1],
            'label': 'Some Location',
            'latitude': '30',
            'longitude': '40'}
        # Send request
        response = Client().post(url, {**query, **credentials})
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['error_message'] == 'Passwords do not match.'
        assert response.context['query'] == query
        # User NOT registered
        assert len(User.objects.filter(username=credentials['username'])) == 0

    def test_register_existing_user(self):
        # Set up user account
        credentials = {
            'username': 'new user',
            'password': '123456'}
        User.objects.create_user(**credentials)
        # Set up request
        url = reverse('register_user')
        display_mode = {'display_mode': get_display_modes()[1]}
        location_params = {
            'label': 'Some Location',
            'latitude': '30',
            'longitude': '40'}
        query = {
            **display_mode,
            **location_params,
            'username': credentials['username'],
            'password1': credentials['password'],
            'password2': credentials['password']}
        # Send request
        response = Client().post(url, query)
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        self.assertEquals(
            response.context['error_message'],
            'User already exists. Please choose different username.')
        self.assertEquals(
            response.context['query'],
            {**display_mode, **location_params})

    def test_register_new_user(self):
        # Set up request
        url = reverse('register_user')
        display_mode = {'display_mode': get_display_modes()[1]}
        location_params = {
            'label': 'Some Location',
            'latitude': '30',
            'longitude': '40'}
        credentials = {
            'username': 'new user',
            'password1': '123456',
            'password2': '123456'}
        query = {
            **display_mode,
            **location_params,
            **credentials}
        # Set up test client
        client = Client()
        # Send request
        response = client.post(url, query)
        # Test response
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        self.assertEquals(
            response.context['success_message'],
            'Your account has been created successfully.')
        self.assertEquals(
            response.context['query'],
            {**display_mode, **location_params})
        # New user successfully registered and logged in
        assert auth.get_user(client).is_authenticated
        assert authenticate(
            username=credentials['username'],
            password=credentials['password1'])


class TestLoginUser(TestCase):

    def test_login_page_with_query(self):
        # Set up request
        url = reverse('login_user')
        location_params = sample_location_params_1()
        request = RequestFactory().get(url, location_params)
        request.user = AnonymousUser()
        response = login_user(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/login_user.html'):
            response.render()
        assert response.context_data['location'] == location_params
        assert response.context_data['next_url'] == None

    def test_login_page_with_no_query(self):
        url = reverse('login_user')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = login_user(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/login_user.html'):
            response.render()
        assert response.context_data['location'] == {}
        assert response.context_data['next_url'] == None

    def test_login_user_with_correct_credentials_with_no_query(self):
        login_page_url = reverse('login_user')
        dashboard_url = reverse('dashboard')
        credentials = sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        response = client.post(login_page_url, credentials)
        self.assertRedirects(response, dashboard_url)
        assert auth.get_user(client).is_authenticated

    def test_login_user_with_correct_credentials_with_query(self):
        location_params = sample_location_params_1()
        login_page_url = reverse('login_user')
        dashboard_url = reverse('dashboard')
        credentials = sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        response = client.post(
            login_page_url,
            {**credentials, **location_params})
        self.assertRedirects(
            response,
            f'{dashboard_url}?{urlencode(location_params)}')
        assert auth.get_user(client).is_authenticated

    def test_login_user_with_bad_credentials_with_no_query(self):
        login_page_url = reverse('login_user')
        credentials = sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        bad_credentials = {
            'username': 'roman',
            'password': 'bad_password'}
        response = client.post(login_page_url, bad_credentials)
        self.assertTemplateUsed(response, 'weather_app/login_user.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['location'] == {}
        assert not auth.get_user(client).is_authenticated

    def test_login_user_with_bad_credentials_with_query(self):
        location_params = sample_location_params_1()
        login_page_url = reverse('login_user')
        credentials = sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        bad_credentials = {
            'username': 'roman',
            'password': 'bad_password'}
        response = client.post(
            login_page_url, {**bad_credentials, **location_params})
        self.assertTemplateUsed(response, 'weather_app/login_user.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['location'] == location_params
        assert not auth.get_user(client).is_authenticated

    # def test_login_required_decorator(self):
    #     location_params = sample_location_params_1()
    #     login_page_url = reverse('login_user')
    #     next_url = reverse('user_profile')
    #     credentials = sample_credentials()
    #     User.objects.create_user(**credentials)
    #     client = Client()
    #     response = client.post(
    #         login_page_url,
    #         {**credentials,
    #          **location_params,
    #          'next_url': next_url})
    #     self.assertRedirects(
    #         response,
    #         f'{next_url}?{urlencode(location_params)}')
    #     assert auth.get_user(client).is_authenticated


class TestLogoutUser(TestCase):

    def test_logout_with_query(self):
        location_params = sample_location_params_1()
        logout_url = reverse('logout_user')
        dashboard_uri = f"{reverse('dashboard')}?{urlencode(location_params)}"
        credentials = sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        client.login(**credentials)
        assert auth.get_user(client).is_authenticated
        response = client.post(logout_url, location_params)
        assert not auth.get_user(client).is_authenticated
        self.assertRedirects(response, dashboard_uri)

    def test_logout_with_no_query(self):
        credentials = sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        client.login(**credentials)
        assert auth.get_user(client).is_authenticated
        response = client.post(reverse('logout_user'))
        assert not auth.get_user(client).is_authenticated
        self.assertRedirects(response, reverse('dashboard'))


class TestUserProfile(TestCase):

    def test_show_user_profile_with_login(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        client = Client()
        client.login(**credentials)
        response = client.get(profile_url, location_params)
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        assert response.context['location'] == location_params

    def test_show_user_profile_with_no_login(self):
        user = AnonymousUser()
        profile_url = reverse('user_profile')
        login_url = reverse('login_user')
        location_params = sample_location_params_1()
        location_qs = quote_plus(urlencode(location_params))
        response = Client().get(profile_url, location_params)
        redirect_uri = f"{login_url}?next_url={profile_url}%3F{location_qs}"
        self.assertRedirects(response, redirect_uri)

    def test_change_password(self):
        original_credentials = sample_credentials()
        user = User.objects.create_user(**original_credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        client = Client()
        client.login(**original_credentials)
        response = client.post(
            profile_url, {
                **original_credentials,
                'new_password1': 'new_password',
                'new_password2': 'new_password',
                **location_params})
        assert authenticate(
            username=original_credentials['username'],
            password='new_password')
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['success_message'],
            'New password has been set successfully.')
        assert response.context['location'] == location_params

    def test_change_password_with_bad_credentials(self):
        original_credentials = sample_credentials()
        user = User.objects.create_user(**original_credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        client = Client()
        client.login(**original_credentials)
        response = client.post(
            profile_url, {
                'username': original_credentials['username'],
                'password': 'bad_password',
                'new_password1': 'new_password',
                'new_password2': 'new_password',
                **location_params})
        assert authenticate(**original_credentials)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['location'] == location_params

    def test_change_password_to_the_same_password(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                **credentials,
                'new_password1': credentials['password'],
                'new_password2': credentials['password'],
                **location_params})
        assert authenticate(**credentials)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['error_message'],
            'New password must be different from the old one.')
        assert response.context['location'] == location_params

    def test_change_password_with_unmatched_new_passwords(self):
        original_credentials = sample_credentials()
        user = User.objects.create_user(**original_credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        client = Client()
        client.login(**original_credentials)
        response = client.post(
            profile_url, {
                **original_credentials,
                'new_password1': 'new_password',
                'new_password2': 'bad_password',
                **location_params})
        assert authenticate(**original_credentials)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['error_message'],
            'New passwords do not match.')
        assert response.context['location'] == location_params

    def test_delete_location_history_with_bad_credentials(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        actual_location_params = sample_location_params_1()
        location = Location(**actual_location_params, user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                'username': credentials['username'],
                'password': 'bad_password',
                **actual_location_params,
                'clear_history': True})
        assert location in Location.objects.all()
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['location'] == actual_location_params

    def test_delete_location_history_except_favorites(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        actual_location_params = sample_location_params_1()
        actual_location = Location(**actual_location_params, user=user)
        actual_location.save()
        favorite_location = Location(
            label='Favorite Place',
            latitude=70,
            longitude=80,
            is_favorite=True,
            user=user)
        favorite_location.save()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                **credentials,
                **actual_location_params,
                'preserve_favorites': True,
                'clear_history': True})
        remaining_locations = Location.objects.all()
        assert not actual_location in remaining_locations
        assert favorite_location in remaining_locations
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['success_message'],
            'Your location history except favorites has been deleted.')
        assert response.context['location'] == actual_location_params

    def test_delete_location_history_completely(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        actual_location_params = sample_location_params_1()
        actual_location = Location(**actual_location_params, user=user)
        actual_location.save()
        favorite_location = Location(
            label='Favorite Place',
            latitude=70,
            longitude=80,
            is_favorite=True,
            user=user)
        favorite_location.save()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                **credentials,
                **actual_location_params,
                'clear_history': True})
        assert len(Location.objects.all()) == 0
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['success_message'],
            'Your location history has been deleted completely.')
        assert response.context['location'] == actual_location_params

    def test_delete_user_account(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        location = Location(**location_params, user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                **credentials,
                **location_params,
                'delete_account': True,
                'i_am_sure': True})
        assert len(User.objects.all()) == 0
        assert len(Location.objects.all()) == 0
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['success_message'],
            'Your user account has been deleted completely.')
        assert response.context['location'] == location_params

    def test_delete_user_account_without_confirmation(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        location = Location(**location_params, user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                **credentials,
                **location_params,
                'delete_account': True,
                # Missing 'i_am_sure': True
                # Template normally prevents such a request
            })
        assert user in User.objects.all()
        assert location in Location.objects.all()
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['error_message'],
            'Invalid options.')
        assert response.context['location'] == location_params

    def test_delete_user_account_with_bad_credentials(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        profile_url = reverse('user_profile')
        location_params = sample_location_params_1()
        location = Location(**location_params, user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        response = client.post(
            profile_url, {
                'username': credentials['username'],
                'password': 'bad_password',
                **location_params,
                'delete_account': True,
                'i_am_sure': True})
        assert user in User.objects.all()
        assert location in Location.objects.all()
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/user_profile.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['location'] == location_params


class TestUtils(TestCase):

    def test_get_location_params_from_GET_with_query(self):
        url = reverse('dashboard')
        location_params = sample_location_params_1()
        request = RequestFactory().get(url, location_params)
        assert get_location_params(request) == location_params

    def test_get_location_params_from_GET_with_no_query(self):
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        assert get_location_params(request) == {}

    def test_get_location_params_from_POST_with_query(self):
        url = reverse('dashboard')
        location_params = sample_location_params_1()
        request = RequestFactory().post(url, location_params)
        assert get_location_params(request) == location_params

    def test_get_location_params_from_POST_with_no_query(self):
        url = reverse('dashboard')
        request = RequestFactory().post(url)
        assert get_location_params(request) == {}

    def test_get_location_history_with_login(self):
        user = sample_user()
        user.save()
        location = sample_location_instance_1()
        location.user = user
        location.save()
        location_history = get_location_history(user)
        assert location_history[0] == location
        assert len(location_history) == 1

    def test_get_location_history_with_no_login(self):
        user_1 = sample_user()
        user_1.save()
        location = sample_location_instance_1()
        location.user = user_1
        location.save()
        user_2 = AnonymousUser()
        location_history = get_location_history(user_2)
        assert location_history == None

    def test_get_favorite_locations_with_login(self):
        user = sample_user()
        user.save()
        ordinary_location = Location(
            label='Common Location',
            latitude=30.0,
            longitude=40.0,
            user=user)
        ordinary_location.save()
        favorite_location = Location(
            label='Favorite Location',
            latitude=50.0,
            longitude=60.0,
            is_favorite=True,
            user=user)
        favorite_location.save()
        favorites = get_favorite_locations(user)
        assert len(favorites) == 1
        assert ordinary_location not in favorites
        assert favorite_location in favorites

    def test_get_favorite_locations_with_no_login(self):
        user_1 = sample_user()
        user_1.save()
        ordinary_location = Location(
            label='Common Location',
            latitude=30.0,
            longitude=40.0,
            user=user_1)
        ordinary_location.save()
        favorite_location = Location(
            label='Favorite Location',
            latitude=50.0,
            longitude=60.0,
            is_favorite=True,
            user=user_1)
        favorite_location.save()
        user_2 = AnonymousUser()
        favorites = get_favorite_locations(user_2)
        assert favorites == None

    # def test_redirect_to_dashboard_with_query(self):
    #     # https://docs.djangoproject.com/en/3.2/ref/request-response/
    #     base_url = reverse('dashboard')
    #     location_params = sample_location_params_1()
    #     query_string = urlencode(location_params)
    #     uri = f'{base_url}?{query_string}'
    #     response = redirect_to_dashboard(location_params)
    #     assert response.status_code == 302
    #     assert response.url == uri

    # def test_redirect_to_dashboard_with_no_query(self):
    #     # https://docs.djangoproject.com/en/3.2/ref/request-response/
    #     response = redirect_to_dashboard()
    #     assert response.status_code == 302
    #     assert response.url == reverse('dashboard')

    def test_render_dashboard_with_no_query_with_no_login(self):
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = render_dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/search_location.html'):
            response.render()
        assert response.context_data['favorite_locations'] == None
        assert response.context_data['location_history'] == None

    def test_render_dashboard_with_query_with_login(self):
        url = reverse('dashboard')
        location_params = sample_location_params_1()
        request = RequestFactory().get(url, location_params)
        request.user = sample_user()
        location = sample_location_instance_1()
        weather = sample_weather()
        air_pollution = sample_air_pollution()
        charts = sample_charts()
        response = render_dashboard(
            request, location, weather, air_pollution, charts)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/dashboard.html'):
            response.render()
        assert response.context_data['location'] == location
        assert response.context_data['weather'] == weather
        assert response.context_data['air_pollution'] == air_pollution
        assert response.context_data['charts'] == charts
        assert isinstance(
            response.context_data['favorite_locations'], QuerySet)
        assert isinstance(
            response.context_data['location_history'], QuerySet)
