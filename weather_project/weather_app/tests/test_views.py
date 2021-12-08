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
        query = get_test_location_query()
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/dashboard.html')
        assert len(list(response.context['messages'])) == 0
        check_context_with_location_query(response.context, query)
        check_context_with_user_data(response.context, user_data)

    def test_dashboard_with_no_query_with_login(self):
        user_data = setup_test_user_data()
        client = Client()
        client.login(**user_data['credentials'])
        url = reverse('dashboard')
        response = client.get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/search_location.html')
        assert len(list(response.context['messages'])) == 0
        check_context_with_no_query(response.context)
        check_context_with_user_data(response.context, user_data)

    def test_dashboard_with_location_query_with_no_login(self):
        url = reverse('dashboard')
        query = get_test_location_query()
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/dashboard.html')
        assert len(list(response.context['messages'])) == 0
        check_context_with_location_query(response.context, query)
        check_context_with_no_user_data(response.context)

    def test_dashboard_with_no_query_with_no_login(self):
        response = Client().get(reverse('dashboard'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/search_location.html')
        assert len(list(response.context['messages'])) == 0
        check_context_with_no_query(response.context)
        check_context_with_no_user_data(response.context)

    def test_dashboard_with_weather_API_timeout(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_location_query()
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = dashboard(request, weather_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Weather service time out')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_weather_API_http_error(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_location_query()
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = dashboard(request, weather_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Weather service error')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_air_pollution_API_timeout(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_location_query()
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = dashboard(request, air_pltn_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Air pollution service time out')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_air_pollution_API_http_error(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_location_query()
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = dashboard(request, air_pltn_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Air pollution service error')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)

    def test_dashboard_with_incorrect_location_query(self):
        user_data = setup_test_user_data()
        url = reverse('dashboard')
        query = get_test_location_query()
        query['latitude'] = '91'  # Out of range
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
        check_context_with_message(response.context, query)
        check_context_with_user_data(response.context, user_data)

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

    def test_search_location_with_too_many_matches(self):
        user_data = setup_test_user_data()
        url = reverse('search_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': 'Lhota'}
        lhota = {
            'label': 'Lhota, OK, Czechia',
            'latitude': 49.71667,
            'longitude': 17.28333}
        client = Client()
        client.login(**user_data['credentials'])
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        messages = list(response.context['messages'])
        # Search results message
        assert len(messages) == 1
        message = messages[0].message
        self.assertEquals(message['header'], 'Select location')
        self.assertEquals(message['description'],
                          'Showing only first 20 matching locations:')
        assert lhota in message['search_results']
        assert len(message['search_results']) == 20
        check_context_with_message(response.context, query)
        check_context_with_user_data(response.context, user_data)

    def test_search_location_with_multiple_matches(self):
        user_data = setup_test_user_data()
        url = reverse('search_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': 'Praha'}
        praha = {
            'label': 'Prague, Czechia',
            'latitude': 50.06694,
            'longitude': 14.460249}
        client = Client()
        client.login(**user_data['credentials'])
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        messages = list(response.context['messages'])
        # Search results message
        assert len(messages) == 1
        message = messages[0].message
        assert message['header'] == 'Select location'
        assert message['description'] == None
        assert praha in message['search_results']
        assert len(message['search_results']) > 3
        check_context_with_message(response.context, query)
        check_context_with_user_data(response.context, user_data)

    def test_search_location_with_single_match(self):
        url = reverse('search_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': 'Růžďka'}
        response = Client().get(url, query)
        redirect_query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': '',
            'label': 'Růžďka, ZK, Czechia',
            'latitude': '49.39395',
            'longitude': '17.99559'}
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)

    def test_search_location_without_match(self):
        user_data = setup_test_user_data()
        url = reverse('search_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': 'incorrect_location_name'}
        client = Client()
        client.login(**user_data['credentials'])
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        messages = list(response.context['messages'])
        # "Location not found" message
        assert len(messages) == 1
        message = messages[0].message
        assert message['header'] == 'Location not found'
        assert message['search_results'] == None
        check_context_with_message(response.context, query)
        check_context_with_user_data(response.context, user_data)

    def test_search_location_with_no_query(self):
        response = Client().get(reverse('search_location'))
        expected_query = {
            'display_mode': get_valid_display_modes()[0],
            'label': '',
            'latitude': '',
            'longitude': ''}
        redirect_uri = f"{reverse('dashboard')}?{urlencode(expected_query)}"
        # Redirected to search page
        self.assertRedirects(response, redirect_uri)

    def test_search_location_with_API_timeout(self):
        user_data = setup_test_user_data()
        url = reverse('search_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': 'Brno'}
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = search_location(request, ORS_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service time out')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)

    def test_search_location_with_API_http_error(self):
        user_data = setup_test_user_data()
        url = reverse('search_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'search_text': 'Brno'}
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = search_location(request, ORS_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service error')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)


class TestRandomLocation(TestCase):
    # Location API docs:
    # https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get

    def test_show_random_location(self):
        url = reverse('random_location')
        query = {'display_mode': get_valid_display_modes()[1]}
        response = Client().get(url, query)
        assert response.status_code == 302
        # Analyze redirect URI
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

    def test_show_random_location_with_API_timeout(self):
        url = reverse('random_location')
        query = {'display_mode': get_valid_display_modes()[1]}
        user_data = setup_test_user_data()
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = random_location(request, ORS_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service time out')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)

    def test_show_random_location_with_API_http_error(self):
        url = reverse('random_location')
        query = {'display_mode': get_valid_display_modes()[1]}
        user_data = setup_test_user_data()
        request, messages = setup_get_request_with_messages(
            url, query, user_data['user'])
        response = random_location(request, ORS_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        # Error message
        assert len(list(messages)) == 1
        self.assertEquals(
            list(messages)[0].message['header'],
            'Location service error')
        check_context_with_message(response.context_data, query)
        check_context_with_user_data(response.context_data, user_data)


class TestUpdateLocation(TestCase):

    def test_add_favorite_location_with_login(self):
        user_data = setup_test_user_data()
        client = Client()
        client.login(**user_data['credentials'])
        url = reverse('update_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'label': user_data['ordinary_location'].label,
            'latitude': str(user_data['ordinary_location'].latitude),
            'longitude': str(user_data['ordinary_location'].longitude),
            'location_id': str(user_data['ordinary_location'].id),
            'is_favorite': True}  # Add the location to favorites
        response = client.post(url, query)
        # Location added to favorites
        updated_location = Location.objects.get(
            pk=user_data['ordinary_location'].id)
        assert updated_location.is_favorite
        query.pop('location_id')
        query.pop('is_favorite')
        # Redirected back to dashboard
        redirect_uri = f"{reverse('dashboard')}?{urlencode(query)}"
        self.assertRedirects(response, redirect_uri)

    def test_remove_favorite_location_with_login(self):
        user_data = setup_test_user_data()
        client = Client()
        client.login(**user_data['credentials'])
        url = reverse('update_location')
        query = {
            'display_mode': get_valid_display_modes()[1],
            'label': user_data['favorite_location'].label,
            'latitude': str(user_data['favorite_location'].latitude),
            'longitude': str(user_data['favorite_location'].longitude),
            'location_id': str(user_data['favorite_location'].id),
            'is_favorite': False}  # Remove the location from favorites
        response = client.post(url, query)
        # Location removed from favorites
        updated_location = Location.objects.get(
            pk=user_data['favorite_location'].id)
        assert not updated_location.is_favorite
        query.pop('location_id')
        query.pop('is_favorite')
        # Redirected back to dashboard
        redirect_uri = f"{reverse('dashboard')}?{urlencode(query)}"
        self.assertRedirects(response, redirect_uri)

    def test_add_favorite_location_with_no_login(self):
        user_data = setup_test_user_data()
        url = reverse('update_location')
        # Correct query
        query = {
            'display_mode': get_valid_display_modes()[1],
            'label': user_data['ordinary_location'].label,
            'latitude': str(user_data['ordinary_location'].latitude),
            'longitude': str(user_data['ordinary_location'].longitude),
            'location_id': str(user_data['ordinary_location'].id),
            'is_favorite': True}  # Try to add the location to favorites
        # User NOT logged in
        response = Client().post(url, query)
        # Location NOT updated
        updated_location = Location.objects.get(
            pk=user_data['ordinary_location'].id)
        assert not updated_location.is_favorite
        query.pop('location_id')
        query.pop('is_favorite')
        # Redirected to login page
        redirect_uri = f"{reverse('login_user')}?{urlencode(query)}"
        self.assertRedirects(response, redirect_uri)


class TestRegisterUser(TestCase):

    def test_show_user_registration_page_with_location_query(self):
        url = reverse('register_user')
        query = get_test_location_query()
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['query'] == query

    def test_show_user_registration_page_with_no_location_query(self):
        response = Client().get(reverse('register_user'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['query'] == {
            'display_mode': get_valid_display_modes()[0],
            'search_text': '',
            'label': '',
            'latitude': '',
            'longitude': ''}

    def test_register_new_user_with_unmatched_passwords(self):
        url = reverse('register_user')
        credentials = {
            'username': 'new user',
            'password1': '1234567890',
            'password2': '12345678'}
        location_query = get_test_location_query()
        response = Client().post(url, {**location_query, **credentials})
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['error_message'] == 'Passwords do not match.'
        assert response.context['query'] == {
            **location_query,
            'search_text': ''}
        assert len(User.objects.filter(username=credentials['username'])) == 0

    def test_register_existing_user(self):
        url = reverse('register_user')
        user = User.objects.create_user(
            username='new user',
            password='12345678')
        credentials = {
            'username': 'new user',
            'password1': '12345678',
            'password2': '12345678'}
        location_query = get_test_location_query()
        response = Client().post(url, {**location_query, **credentials})
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        self.assertEquals(
            response.context['error_message'],
            'User already exists. Please choose different username.')
        self.assertEquals(response.context['query'], location_query)

    def test_register_new_user(self):
        url = reverse('register_user')
        credentials = {
            'username': 'new user',
            'password1': '12345678',
            'password2': '12345678'}
        location_query = get_test_location_query()
        response = Client().post(url, {**location_query, **credentials})
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        self.assertEquals(
            response.context['success_message'],
            'Your account has been created successfully.')
        self.assertEquals(response.context['query'], location_query)


class TestLoginUser(TestCase):

    def test_show_login_page_with_location_query(self):
        url = reverse('login_user')
        query = get_test_location_query()
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/login_user.html')
        assert response.context['query'] == query

    def test_show_login_page_with_no_query(self):
        response = Client().get(reverse('login_user'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/login_user.html')
        assert response.context['query'] == get_empty_location_query()

    def test_login_user_with_no_location_query(self):
        url = reverse('login_user')
        credentials = get_test_user_credentials()
        user = User.objects.create_user(**credentials)
        client = Client()
        response = client.post(url, credentials)
        redirect_url = reverse('dashboard')
        redirect_query = get_empty_location_query()
        redirect_uri = f"{redirect_url}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)
        assert auth.get_user(client).is_authenticated
        assert auth.get_user(client) == user

    def test_login_user_with_location_query(self):
        url = reverse('login_user')
        location_query = get_test_location_query()
        credentials = get_test_user_credentials()
        user = User.objects.create_user(**credentials)
        client = Client()
        response = client.post(url, {**credentials, **location_query})
        redirect_url = reverse('dashboard')
        redirect_uri = f"{redirect_url}?{urlencode(location_query)}"
        self.assertRedirects(response, redirect_uri)
        assert auth.get_user(client).is_authenticated
        assert auth.get_user(client) == user

    def test_login_user_with_bad_credentials_with_no_query(self):
        url = reverse('login_user')
        user = User.objects.create_user(
            username='test_user',
            password='12345678')
        bad_dredentials = {
            'username': 'test_user',
            'password': 'bad_password'}
        client = Client()
        response = client.post(url, bad_dredentials)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/login_user.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['query'] == get_empty_location_query()
        assert not auth.get_user(client).is_authenticated

    def test_login_user_with_bad_credentials_with_query(self):
        url = reverse('login_user')
        location_query = get_test_location_query()
        user = User.objects.create_user(
            username='test_user',
            password='12345678')
        bad_dredentials = {
            'username': 'test_user',
            'password': 'bad_password'}
        client = Client()
        response = client.post(url, {**bad_dredentials, **location_query})
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/login_user.html')
        self.assertEquals(
            response.context['error_message'],
            'Username and password do not match.')
        assert response.context['query'] == location_query
        assert not auth.get_user(client).is_authenticated


class TestLogoutUser(TestCase):

    def test_logout_with_query(self):
        location_params = sample_location_params_1()
        logout_url = reverse('logout_user')
        dashboard_uri = f"{reverse('dashboard')}?{urlencode(location_params)}"
        credentials = get_test_user_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        client.login(**credentials)
        assert auth.get_user(client).is_authenticated
        response = client.post(logout_url, location_params)
        assert not auth.get_user(client).is_authenticated
        self.assertRedirects(response, dashboard_uri)

    def test_logout_with_no_query(self):
        credentials = get_test_user_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        client.login(**credentials)
        assert auth.get_user(client).is_authenticated
        response = client.post(reverse('logout_user'))
        assert not auth.get_user(client).is_authenticated
        self.assertRedirects(response, reverse('dashboard'))


class TestUserProfile(TestCase):

    def test_show_user_profile_with_login(self):
        credentials = get_test_user_credentials()
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
        original_credentials = get_test_user_credentials()
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
        original_credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
        original_credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
        credentials = get_test_user_credentials()
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
