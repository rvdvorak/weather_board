from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, Client, RequestFactory
from weather_app.views import *
from datetime import datetime
import pytz
import copy
from django.urls import reverse
from urllib.parse import urlencode, urlparse, parse_qs
from django.test import RequestFactory, Client
import json
import pickle
from weather_app.models import User, Location
from requests.exceptions import Timeout, HTTPError
from django.db.models.query import QuerySet


class TestViews(TestCase):
    def get_sample_location_params(self):
        return {
            'latitude': '-16.3667',
            'longitude': '-58.4',
            'label': 'San Matías, SC, Bolivia'}

    def get_sample_timezone(self):
        return pytz.timezone('America/La_Paz')

    def get_sample_location_instance(self):
        location_params = self.get_sample_location_params()
        return Location(
            latitude=float(location_params['latitude']),
            longitude=float(location_params['longitude']),
            label=location_params['label'])

    def get_sample_credentials(self):
        return {
            'username': 'roman',
            'password': '123456'}
    
    def get_sample_user(self):
        return User(**self.get_sample_credentials())

    def get_current_weather_keys(self):
        return {
            'dt', 'temp', 'feels_like', 'pressure', 'humidity', 'dew_point',
            'clouds', 'uvi', 'visibility', 'wind_speed', 'wind_deg', 'weather'}

    def get_sample_weather(self):
        with open('weather_app/tests/sample_data/weather.pkl', 'rb') as file:
            return pickle.load(file)

    def get_sample_air_pollution(self):
        with open('weather_app/tests/sample_data/air_pollution.pkl', 'rb') as file:
            return pickle.load(file)

    def get_sample_charts(self):
        with open('weather_app/tests/sample_data/charts.pkl', 'rb') as file:
            return pickle.load(file)

    def get_sample_location_history(self):
        with open('weather_app/tests/sample_data/location_history.pkl', 'rb') as file:
            return pickle.load(file)

    def get_sample_favorite_locations(self):
        with open('weather_app/tests/sample_data/favorite_locations.pkl', 'rb') as file:
            pickle.load(file)

    # Testing VIEWS

    def test_show_random_location(self):
        client = Client()
        response = client.get(reverse('random_location'))
        parsed_uri = urlparse(response.url)
        query_string = parsed_uri.query
        params = parse_qs(query_string)
        label = params['label'][0]
        latitude = float(params['latitude'][0])
        longitude = float(params['longitude'][0])
        assert label not in ['', None]
        assert -90.0 <= latitude <= 90.0
        assert -180.0 <= longitude <= 180.0
        assert response.status_code == 302
    
    def test_logout_with_location(self):
        location_params = self.get_sample_location_params()
        logout_url = reverse('logout_user')
        dashboard_uri = f"{reverse('dashboard')}?{urlencode(location_params)}"
        credentials = self.get_sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        client.login(**credentials)
        assert auth.get_user(client).is_authenticated
        response = client.post(logout_url, location_params)
        assert not auth.get_user(client).is_authenticated
        self.assertRedirects(response, dashboard_uri)

    def test_logout_without_location(self):
        credentials = self.get_sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        client.login(**credentials)
        assert auth.get_user(client).is_authenticated
        response = client.post(reverse('logout_user'))
        assert not auth.get_user(client).is_authenticated
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_page_with_location(self):
        url = reverse('login_user')
        location_params = self.get_sample_location_params()
        request = RequestFactory().get(url, location_params)
        request.user = AnonymousUser()
        response = login_user(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/login_user.html'):
            response.render()
        assert response.context_data == {'location_params': location_params}

    def test_login_page_without_location(self):
        url = reverse('login_user')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = login_user(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/login_user.html'):
            response.render()
        assert response.context_data == {'location_params': {}}

    def test_login_user_with_correct_credentials_without_location(self):
        login_page_url = reverse('login_user')
        dashboard_url = reverse('dashboard')
        credentials = self.get_sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        response = client.post(login_page_url, credentials)
        self.assertRedirects(response, dashboard_url)
        assert auth.get_user(client).is_authenticated

    def test_login_user_with_correct_credentials_with_location(self):
        location_params = self.get_sample_location_params()
        login_page_url = reverse('login_user')
        dashboard_url = reverse('dashboard')
        credentials = self.get_sample_credentials()
        User.objects.create_user(**credentials)
        client = Client()
        response = client.post(
            login_page_url,
            {**credentials, **location_params})
        self.assertRedirects(
            response,
            f'{dashboard_url}?{urlencode(location_params)}')
        assert auth.get_user(client).is_authenticated

    def test_login_user_with_bad_credentials_without_location(self):
        login_page_url = reverse('login_user')
        credentials = self.get_sample_credentials()
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
        assert response.context['location_params'] == {}
        assert not auth.get_user(client).is_authenticated

    def test_login_user_with_bad_credentials_with_location(self):
        location_params = self.get_sample_location_params()
        login_page_url = reverse('login_user')
        credentials = self.get_sample_credentials()
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
        assert response.context['location_params'] == location_params
        assert not auth.get_user(client).is_authenticated

    def test_dashboard_without_location_logged_out(self):
        user = AnonymousUser()
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        request.user = user
        response = dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/dashboard.html'):
            response.render()
        assert response.context_data == {
            'location': None,
            'weather': None,
            'air_pollution': None,
            'charts': None,
            'favorite_locations': None,
            'location_history': None}

    def test_dashboard_without_location_logged_in(self):
        user = self.get_sample_user()
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        request.user = user
        response = dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/dashboard.html'):
            response.render()
        assert response.context_data['location'] == None
        assert response.context_data['weather'] == None
        assert response.context_data['air_pollution'] == None
        assert response.context_data['charts'] == None
        assert isinstance(
            response.context_data['favorite_locations'], QuerySet)
        assert isinstance(
            response.context_data['location_history'], QuerySet)

    def test_dashboard_with_location_logged_out(self):
        user = AnonymousUser()
        location_params = self.get_sample_location_params()
        url = reverse('dashboard')
        timezone = self.get_sample_timezone()
        request = RequestFactory().get(url, location_params)
        request.user = user
        response = dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/dashboard.html'):
            response.render()
        location = response.context_data['location']
        assert location.label == location_params['label']
        assert location.latitude == float(location_params['latitude'])
        assert location.longitude == float(location_params['longitude'])
        weather = response.context_data['weather']
        assert weather['lat'] == float(location_params['latitude'])
        assert weather['lon'] == float(location_params['longitude'])
        assert pytz.timezone(weather['timezone']) == timezone
        air_pollution = response.context_data['air_pollution']
        assert air_pollution['coord']['lat'] == float(
            location_params['latitude'])
        assert air_pollution['coord']['lon'] == float(
            location_params['longitude'])
        charts = response.context_data['charts']
        assert charts.keys() == {'minutely', 'hourly', 'daily'}
        assert response.context_data['favorite_locations'] == None
        assert response.context_data['location_history'] == None

    def test_dashboard_with_location_logged_in(self):
        user = self.get_sample_user()
        user.save()  # Necessary in this test
        location_params = self.get_sample_location_params()
        url = reverse('dashboard')
        timezone = self.get_sample_timezone()
        request = RequestFactory().get(url, location_params)
        request.user = user
        response = dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/dashboard.html'):
            response.render()
        location = response.context_data['location']
        assert location.label == location_params['label']
        assert location.latitude == float(location_params['latitude'])
        assert location.longitude == float(location_params['longitude'])
        weather = response.context_data['weather']
        assert weather['lat'] == float(location_params['latitude'])
        assert weather['lon'] == float(location_params['longitude'])
        assert pytz.timezone(weather['timezone']) == timezone
        air_pollution = response.context_data['air_pollution']
        assert air_pollution['coord']['lat'] == float(
            location_params['latitude'])
        assert air_pollution['coord']['lon'] == float(
            location_params['longitude'])
        charts = response.context_data['charts']
        assert charts.keys() == {'minutely', 'hourly', 'daily'}
        assert isinstance(
            response.context_data['favorite_locations'], QuerySet)
        assert isinstance(response.context_data['location_history'], QuerySet)

    # Testing UTILS

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

    def test_redirect_to_dashboard_with_location(self):
        # https://docs.djangoproject.com/en/3.2/ref/request-response/
        base_url = reverse('dashboard')
        location_params = self.get_sample_location_params()
        query_string = urlencode(location_params)
        uri = f'{base_url}?{query_string}'
        response = redirect_to_dashboard(location_params)
        assert response.status_code == 302
        assert response.url == uri

    def test_redirect_to_dashboard_without_location(self):
        # https://docs.djangoproject.com/en/3.2/ref/request-response/
        response = redirect_to_dashboard()
        assert response.status_code == 302
        assert response.url == reverse('dashboard')

    def test_render_dashboard_without_location_logged_out(self):
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = render_dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/dashboard.html'):
            response.render()
        assert response.context_data == {
            'location': None,
            'weather': None,
            'air_pollution': None,
            'charts': None,
            'favorite_locations': None,
            'location_history': None}

    def test_render_dashboard_with_location_logged_in(self):
        url = reverse('dashboard')
        location_params = self.get_sample_location_params()
        request = RequestFactory().get(url, location_params)
        request.user = self.get_sample_user()
        location = self.get_sample_location_instance()
        weather = self.get_sample_weather()
        air_pollution = self.get_sample_air_pollution()
        charts = self.get_sample_charts()
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

    def test_get_charts(self):
        weather = self.get_sample_weather()
        charts = self.get_sample_charts()
        assert get_charts(weather) == charts

    def test_render_user_profile_without_location_logged_out(self):
        url = reverse('user_profile')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = render_user_profile(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/user_profile.html'):
            response.render()
        assert response.context_data == {
            'error_message': None,
            'success_message': None,
            'location_params': {},
            'location_history': None,
            'favorite_locations': None}

    def test_render_user_profile_with_location_logged_in_with_messages(self):
        location_params = self.get_sample_location_params()
        url = reverse('user_profile')
        request = RequestFactory().get(url, location_params)
        request.user = self.get_sample_user()
        response = render_user_profile(
            request,
            error_message='error message',
            success_message='success message')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/user_profile.html'):
            response.render()
        assert response.context_data['error_message'] == 'error message'
        assert response.context_data['success_message'] == 'success message'
        assert response.context_data['location_params'] == location_params
        assert isinstance(
            response.context_data['favorite_locations'], QuerySet)
        assert isinstance(
            response.context_data['location_history'], QuerySet)

    def test_get_location_params_from_GET_with_location(self):
        url = reverse('dashboard')
        location_params = self.get_sample_location_params()
        request = RequestFactory().get(url, location_params)
        assert get_location_params(request) == location_params

    def test_get_location_params_from_GET_without_location(self):
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        assert get_location_params(request) == {}

    def test_get_location_params_from_POST_with_location(self):
        url = reverse('dashboard')
        location_params = self.get_sample_location_params()
        request = RequestFactory().post(url, location_params)
        assert get_location_params(request) == location_params

    def test_get_location_params_from_POST_without_location(self):
        url = reverse('dashboard')
        request = RequestFactory().post(url)
        assert get_location_params(request) == {}

    def test_get_random_location_params(self):
        location_params = get_random_location_params(ORS_key)
        assert -90.0 <= location_params['latitude'] <= 90.0
        assert -180.0 <= location_params['longitude'] <= 180.0
        assert (location_params['label']) not in ['', None]
        assert len(location_params) == 3

    def test_get_random_location_params_timeout(self):
        timeout = 0.000001
        self.assertRaises(
            Timeout,
            get_random_location_params,
            ORS_key,
            timeout)

    def test_get_random_location_params_http_error(self):
        ORS_key = 'bad_key'
        self.assertRaises(
            HTTPError,
            get_random_location_params,
            ORS_key)

    def test_get_search_results(self):
        search_query = 'brno cz'
        search_results = get_search_results(search_query, ORS_key)
        assert type(search_results) is list
        assert len(search_results) != 0
        assert search_results[0]['properties']['label'] == 'Brno, JM, Czechia'

    def test_get_search_results_with_bad_search_query(self):
        search_query = 'some_incorrect_location_name'
        search_results = get_search_results(search_query, ORS_key)
        assert search_results == []

    def test_get_search_results_timeout(self):
        search_query = 'brno cz'
        timeout = 0.000001
        self.assertRaises(
            Timeout,
            get_search_results,
            search_query,
            ORS_key,
            timeout)

    def test_get_search_results_http_error(self):
        search_query = 'brno cz'
        ORS_key = 'bad_key'
        self.assertRaises(
            HTTPError,
            get_search_results,
            search_query,
            ORS_key)

    def test_get_location_instance_with_params_logged_in(self):
        location_params = self.get_sample_location_params()
        user = self.get_sample_user()
        user.save()
        location = self.get_sample_location_instance()
        location.user = user
        location.save()
        assert get_location_instance(location_params, user) == location

    def test_get_location_instance_with_params_logged_out(self):
        location_params = self.get_sample_location_params()
        user_1 = self.get_sample_user()
        user_1.save()
        location_1 = self.get_sample_location_instance()
        location_1.user = user_1
        location_1.save()
        user_2 = AnonymousUser()
        location_2 = get_location_instance(location_params, user_2)
        assert location_2.label == location_1.label
        assert location_2.latitude == location_1.latitude
        assert location_2.longitude == location_1.longitude
        assert location_2 != location_1

    def test_get_location_instance_without_params_logged_out(self):
        user = AnonymousUser()
        location_params = {}
        assert get_location_instance(location_params, user) == None

    def test_get_location_instance_without_params_logged_in(self):
        user = self.get_sample_user()
        location_params = {}
        assert get_location_instance(location_params, user) == None

    def test_get_location_history_logged_in(self):
        user = self.get_sample_user()
        user.save()
        location = self.get_sample_location_instance()
        location.user = user
        location.save()
        location_history = get_location_history(user)
        assert location_history[0] == location
        assert len(location_history) == 1

    def test_get_location_history_logged_out(self):
        user_1 = self.get_sample_user()
        user_1.save()
        location = self.get_sample_location_instance()
        location.user = user_1
        location.save()
        user_2 = AnonymousUser()
        location_history = get_location_history(user_2)
        assert location_history == None

    def test_get_favorite_locations_logged_in(self):
        user = self.get_sample_user()
        user.save()
        common_location = Location(
            label='Common Location',
            latitude=30.0,
            longitude=40.0,
            user=user)
        common_location.save()
        favorite_location = Location(
            label='Favorite Location',
            latitude=50.0,
            longitude=60.0,
            is_favorite=True,
            user=user)
        favorite_location.save()
        favorites = get_favorite_locations(user)
        assert len(favorites) == 1
        assert common_location not in favorites
        assert favorite_location in favorites

    def test_get_favorite_locations_logged_out(self):
        user_1 = self.get_sample_user()
        user_1.save()
        common_location = Location(
            label='Common Location',
            latitude=30.0,
            longitude=40.0,
            user=user_1)
        common_location.save()
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

    def test_get_weather(self):
        location = self.get_sample_location_instance()
        timezone = self.get_sample_timezone()
        weather = get_weather(location, OWM_key)
        current_weather_keys = self.get_current_weather_keys()
        # Weather schema https://openweathermap.org/api/one-call-api#parameter
        assert current_weather_keys.issubset(weather['current'].keys())
        assert weather['lat'] == location.latitude
        assert weather['lon'] == location.longitude
        assert pytz.timezone(weather['timezone']) == timezone

    def test_get_weather_timeout(self):
        location = self.get_sample_location_instance()
        timeout = 0.000001
        self.assertRaises(
            Timeout,
            get_weather,
            location,
            OWM_key,
            timeout)

    def test_get_weather_http_error(self):
        location = self.get_sample_location_instance()
        OWM_key = 'bad_key'
        self.assertRaises(
            HTTPError,
            get_weather,
            location,
            OWM_key)

    def test_get_air_pollution(self):
        location = self.get_sample_location_instance()
        timezone = self.get_sample_timezone()
        air_pollution = get_air_pollution(location, timezone, OWM_key)
        components = {'co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3'}
        # Air pollution schema https://openweathermap.org/api/air-pollution#fields
        assert air_pollution.keys() == {'coord', 'list', }
        assert air_pollution['coord']['lat'] == location.latitude
        assert air_pollution['coord']['lon'] == location.longitude
        assert 80 <= len(air_pollution['list']) <= 120
        for item in air_pollution['list']:
            with self.subTest(item=item):
                assert item['components'].keys() == components

    def test_get_air_pollution_timeout(self):
        location = self.get_sample_location_instance()
        timezone = self.get_sample_timezone()
        timeout = 0.000001
        self.assertRaises(
            Timeout,
            get_air_pollution,
            location,
            timezone,
            OWM_key,
            timeout)

    def test_get_air_pollution_http_error(self):
        location = self.get_sample_location_instance()
        timezone = self.get_sample_timezone()
        OWM_key = 'bad_key'
        self.assertRaises(
            HTTPError,
            get_air_pollution,
            location,
            timezone,
            OWM_key)
