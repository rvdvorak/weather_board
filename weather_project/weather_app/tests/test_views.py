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


class TestDashboard(TestCase):
    # Weather API docs:
    # https://openweathermap.org/api/one-call-api#parameter

    # Air pollution API docs:
    # https://openweathermap.org/api/air-pollution#fields

    def test_dashboard_without_query_without_login(self):
        response = Client().get(reverse('dashboard'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/no_location.html')
        assert len(list(response.context['messages'])) == 0
        assert response.context['display_mode'] == display_modes()[0]
        assert response.context['location'] == None
        assert response.context['weather'] == None
        assert response.context['air_pollution'] == None
        assert response.context['charts'] == None
        assert response.context['location_history'] == None
        assert response.context['favorite_locations'] == None

    def test_dashboard_without_query_with_login(self):
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
        client = Client()
        client.login(**credentials)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/no_location.html')
        assert len(list(response.context['messages'])) == 0
        assert response.context['display_mode'] == display_modes()[0]
        assert response.context['location'] == None
        assert response.context['weather'] == None
        assert response.context['air_pollution'] == None
        assert response.context['charts'] == None
        assert favorite_location in response.context['location_history']
        assert ordinary_location in response.context['location_history']
        assert favorite_location in response.context['favorite_locations']
        assert not ordinary_location in response.context['favorite_locations']

    def test_dashboard_with_query_without_login(self):
        url = reverse('dashboard')
        query = {
            'display_mode': display_modes()[1],
            **sample_location_params_1()}
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/dashboard.html')
        assert len(list(response.context['messages'])) == 0
        assert response.context['display_mode'] == display_modes()[1]
        self.assertEquals(
            response.context['location'].label,
            query['label'])
        self.assertEquals(
            response.context['location'].latitude,
            float(query['latitude']))
        self.assertEquals(
            response.context['location'].longitude,
            float(query['longitude']))
        self.assertEquals(
            response.context['weather']['lat'],
            float(query['latitude']))
        self.assertEquals(
            response.context['weather']['lon'],
            float(query['longitude']))
        self.assertEquals(
            pytz.timezone(response.context['weather']['timezone']),
            sample_timezone_1())
        assert required_current_weather_keys().issubset(
            response.context['weather']['current'].keys())
        self.assertEquals(
            response.context['air_pollution']['coord']['lat'],
            float(query['latitude']))
        self.assertEquals(
            response.context['air_pollution']['coord']['lon'],
            float(query['longitude']))
        self.assertEquals(
            response.context['charts'].keys(),
            {'minutely', 'hourly', 'daily', 'air_pollution'})
        assert response.context['location_history'] == None
        assert response.context['favorite_locations'] == None

    def test_dashboard_with_query_with_login(self):
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
        client = Client()
        client.login(**credentials)
        url = reverse('dashboard')
        query = {
            'display_mode': display_modes()[1],
            **sample_location_params_1()}
        response = client.get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/dashboard.html')
        assert len(list(response.context['messages'])) == 0
        assert response.context['display_mode'] == display_modes()[1]
        self.assertEquals(
            response.context['location'].label,
            query['label'])
        self.assertEquals(
            response.context['location'].latitude,
            float(query['latitude']))
        self.assertEquals(
            response.context['location'].longitude,
            float(query['longitude']))
        self.assertEquals(
            response.context['weather']['lat'],
            float(query['latitude']))
        self.assertEquals(
            response.context['weather']['lon'],
            float(query['longitude']))
        self.assertEquals(
            pytz.timezone(response.context['weather']['timezone']),
            sample_timezone_1())
        assert required_current_weather_keys().issubset(
            response.context['weather']['current'].keys())
        self.assertEquals(
            response.context['air_pollution']['coord']['lat'],
            float(query['latitude']))
        self.assertEquals(
            response.context['air_pollution']['coord']['lon'],
            float(query['longitude']))
        self.assertEquals(
            response.context['charts'].keys(),
            {'minutely', 'hourly', 'daily', 'air_pollution'})
        assert favorite_location in response.context['location_history']
        assert ordinary_location in response.context['location_history']
        assert favorite_location in response.context['favorite_locations']
        assert not ordinary_location in response.context['favorite_locations']

    def test_dashboard_with_weather_API_timeout(self):
        base_url = reverse('dashboard')
        query = {
            'display_mode': display_modes()[1],
            **sample_location_params_1()}
        uri = f'{base_url}?{urlencode(query)}'
        request = RequestFactory().get(uri)
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = dashboard(request, weather_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        self.assertEquals(
            list(messages)[0].message['header'],
            'Weather service time out')
        assert response.context_data['display_mode'] == display_modes()[1]
        self.assertEquals(
            response.context_data['location']['label'],
            query['label'])
        self.assertEquals(
            response.context_data['location']['latitude'],
            query['latitude'])
        self.assertEquals(
            response.context_data['location']['longitude'],
            query['longitude'])

    def test_dashboard_with_weather_API_http_error(self):
        location_params = sample_location_params_1()
        uri = f"{reverse('dashboard')}?{urlencode(location_params)}"
        request = RequestFactory().get(uri)
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = dashboard(request, weather_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        self.assertEquals(
            list(messages)[0].message['header'],
            'Weather service error')

    def test_dashboard_with_air_pollution_API_timeout(self):
        location_params = sample_location_params_1()
        uri = f"{reverse('dashboard')}?{urlencode(location_params)}"
        request = RequestFactory().get(uri)
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = dashboard(request, air_pltn_timeout=0.00001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        self.assertEquals(
            list(messages)[0].message['header'],
            'Air pollution service time out')

    def test_dashboard_with_air_pollution_API_http_error(self):
        location_params = sample_location_params_1()
        uri = f"{reverse('dashboard')}?{urlencode(location_params)}"
        request = RequestFactory().get(uri)
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = dashboard(request, air_pltn_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        self.assertEquals(
            list(messages)[0].message['header'],
            'Air pollution service error')

    def test_dashboard_with_bad_location_query(self):
        bad_location_params = {
            'label': 'Bad Location',
            'latitude': '91',  # Out of range
            'longitude': '181'  # Out of range
        }
        response = Client().get(reverse('dashboard'), bad_location_params)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        self.assertEquals(
            list(response.context['messages'])[0].message['header'],
            'Incorrect location parameters')

    #   def test_get_weather(self):
        #     # Weather schema https://openweathermap.org/api/one-call-api#parameter
        #     location = sample_location_instance_1()
        #     timezone = sample_timezone_1()
        #     weather = get_weather(location, OWM_key)
        #     current_weather_keys = {
        #         'dt', 'temp', 'feels_like', 'pressure', 'humidity', 'dew_point',
        #         'clouds', 'uvi', 'visibility', 'wind_speed', 'wind_deg', 'weather'}
        #     assert current_weather_keys.issubset(weather['current'].keys())
        #     assert weather['lat'] == location.latitude
        #     assert weather['lon'] == location.longitude
        #     assert pytz.timezone(weather['timezone']) == timezone

    #   def test_get_weather_timeout(self):
        #     location = sample_location_instance_1()
        #     timeout = 0.000001
        #     self.assertRaises(
        #         Timeout,
        #         get_weather,
        #         location,
        #         OWM_key,
        #         timeout)

    #   def test_get_weather_http_error(self):
        #     location = sample_location_instance_1()
        #     OWM_key = 'bad_key'
        #     self.assertRaises(
        #         HTTPError,
        #         get_weather,
        #         location,
        #         OWM_key)

    #   def test_get_air_pollution(self):
        #     location = sample_location_instance_1()
        #     timezone = sample_timezone_1()
        #     air_pollution = get_air_pollution(location, timezone, OWM_key)
        #     components = {'co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3'}
        #     # Air pollution schema https://openweathermap.org/api/air-pollution#fields
        #     assert air_pollution.keys() == {'coord', 'list', }
        #     assert air_pollution['coord']['lat'] == location.latitude
        #     assert air_pollution['coord']['lon'] == location.longitude
        #     print("len(air_pollution['list'] ==", len(air_pollution['list']))
        #     assert 48 <= len(air_pollution['list']) <= 120
        #     for item in air_pollution['list']:
        #         with self.subTest(item=item):
        #             assert item['components'].keys() == components

    #   def test_get_air_pollution_timeout(self):
        #     location = sample_location_instance_1()
        #     timezone = sample_timezone_1()
        #     timeout = 0.000001
        #     self.assertRaises(
        #         Timeout,
        #         get_air_pollution,
        #         location,
        #         timezone,
        #         OWM_key,
        #         timeout)

    #   def test_get_air_pollution_http_error(self):
        #     location = sample_location_instance_1()
        #     timezone = sample_timezone_1()
        #     OWM_key = 'bad_key'
        #     self.assertRaises(
        #         HTTPError,
        #         get_air_pollution,
        #         location,
        #         timezone,
        #         OWM_key)

    #   def test_convert_timestamps_to_datetimes(self):
        #     # TODO Test timestamps just before/after DST begin/end
        #     utc_timestamp = 1636339065
        #     timezone = pytz.timezone('Europe/Prague')
        #     local_datetime = datetime.fromtimestamp(utc_timestamp, timezone)
        #     keys_to_convert = ['dt', 'sunrise', 'sunset']
        #     input_data = {
        #         'abc': 123456789,
        #         'jkl': [{
        #                 'dt': utc_timestamp,
        #                 'xyz': 987654321,
        #                 'sunrise': utc_timestamp
        #                 }, {
        #                 'sunset': utc_timestamp,
        #                 'def': 123123123,
        #                 'x': [{
        #                     'dt': utc_timestamp,
        #                     'asd': 99999999999,
        #                     'q': {
        #                         'w': 888888888,
        #                         'dt': utc_timestamp,
        #                         'sunrise': utc_timestamp,
        #                         'sunset': utc_timestamp}}]}]}
        #     output_data = {
        #         'abc': 123456789,
        #         'jkl': [{
        #                 'dt': local_datetime,
        #                 'xyz': 987654321,
        #                 'sunrise': local_datetime
        #                 }, {
        #                 'sunset': local_datetime,
        #                 'def': 123123123,
        #                 'x': [{
        #                     'dt': local_datetime,
        #                     'asd': 99999999999,
        #                     'q': {
        #                         'w': 888888888,
        #                         'dt': local_datetime,
        #                         'sunrise': local_datetime,
        #                         'sunset': local_datetime}}]}]}
        #     assert convert_timestamps_to_datetimes(
        #         copy.deepcopy(input_data),
        #         keys_to_convert,
        #         timezone) == output_data
        #     assert convert_timestamps_to_datetimes(
        #         copy.deepcopy([[[input_data]]]),
        #         keys_to_convert,
        #         timezone) == [[[output_data]]]

    #   def test_get_charts(self):
        #     weather = sample_weather()
        #     charts = sample_charts()
        #     assert get_charts(weather) == charts

    #   def test_get_location_instance_with_params_with_login(self):
        #     location_params = sample_location_params_1()
        #     user = sample_user()
        #     user.save()
        #     location = Location(**location_params, user=user)
        #     location.save()
        #     assert get_location_instance(location_params, user) == location

    #   def test_get_location_instance_with_params_without_login(self):
        #     location_params = sample_location_params_1()
        #     user_1 = sample_user()
        #     user_1.save()
        #     location_1 = sample_location_instance_1()
        #     location_1.user = user_1
        #     location_1.save()
        #     user_2 = AnonymousUser()
        #     location_2 = get_location_instance(location_params, user_2)
        #     assert location_2.label == location_1.label
        #     assert location_2.latitude == location_1.latitude
        #     assert location_2.longitude == location_1.longitude
        #     assert location_2 != location_1

    #   def test_get_location_instance_without_params_without_login(self):
        #     user = AnonymousUser()
        #     location_params = {}
        #     assert get_location_instance(location_params, user) == None

    #   def test_get_location_instance_without_params_with_login(self):
        #     user = sample_user()
        #     location_params = {}
        #     assert get_location_instance(location_params, user) == None


class TestSearchLocation(TestCase):
    # Location API docs:
    # https://openrouteservice.org/dev/#/api-docs/geocode/search/get

    def test_search_location_with_too_many_matches_without_login(self):
        url = reverse('search_location')
        query = {
            'display_mode': display_modes()[1],
            'search_query': 'Lhota'}
        lhota = {
            'label': 'Lhota, OK, Czechia',
            'latitude': 49.71667,
            'longitude': 17.28333}
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        message = list(response.context['messages'])[0].message
        assert message['header'] == 'Select location'
        self.assertEquals(
            message['description'],
            'Showing only first 20 matching locations:')
        assert lhota in message['search_results']
        assert len(message['search_results']) == 20
        assert response.context['display_mode'] == display_modes()[1]
        assert response.context['location'] == None
        assert response.context['weather'] == None
        assert response.context['air_pollution'] == None
        assert response.context['charts'] == None
        assert response.context['location_history'] == None
        assert response.context['favorite_locations'] == None
        
    def test_search_location_with_multiple_matches(self):
        url = reverse('search_location')
        query = {
            'display_mode': display_modes()[1],
            'search_query': 'Praha'}
        praha = {
            'label': 'Prague, Czechia',
            'latitude': 50.06694,
            'longitude': 14.460249}
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        message = list(response.context['messages'])[0].message
        assert message['header'] == 'Select location'
        assert praha in message['search_results']
        assert len(message['search_results']) > 3
        assert response.context['display_mode'] == display_modes()[1]
        assert response.context['favorite_locations'] == None
        assert response.context['location_history'] == None

    def test_search_location_with_single_match(self):
        url = reverse('search_location')
        query = {
            'display_mode': display_modes()[1],
            'search_query': 'Růžďka'}
        response = Client().get(url, query)
        redirect_query = {
            'display_mode': display_modes()[1],
            'label': 'Růžďka, ZK, Czechia',
            'latitude': 49.39395,
            'longitude': 17.99559}
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_query)}"
        self.assertRedirects(response, redirect_uri)

    def test_search_location_without_match(self):
        url = reverse('search_location')
        query = {
            'display_mode': display_modes()[1],
            'search_query': 'incorrect_location_name'}
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        message = list(response.context['messages'])[0].message
        assert message['header'] == 'Location not found'
        assert message['search_results'] == None
        assert response.context['display_mode'] == display_modes()[1]

    def test_search_location_without_query(self):
        response = Client().get(reverse('search_location'))
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/messages.html')
        message = list(response.context['messages'])[0].message
        assert message['header'] == 'Nothing to search'
        assert message['search_results'] == None
        assert response.context['display_mode'] == display_modes()[0]

    def test_search_location_with_ORS_timeout(self):
        base_url = reverse('search_location')
        query_string = urlencode({
            'display_mode': display_modes()[1],
            'search_query': 'Praha'})
        uri = f'{base_url}?{query_string}'
        request = RequestFactory().get(uri)
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Send request
        response = search_location(request, ORS_timeout=0.0001)
        # Test response
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        message = list(messages)[0].message
        assert message['header'] == 'Location service time out'
        assert message['search_results'] == None
        assert response.context_data['display_mode'] == display_modes()[1]
        assert response.context_data['favorite_locations'] == None
        assert response.context_data['location_history'] == None

    def test_search_location_with_ORS_http_error(self):
        base_url = reverse('search_location')
        query_string = urlencode({'search_query': 'Praha'})
        uri = f'{base_url}?{query_string}'
        request = RequestFactory().get(uri)
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = search_location(request, ORS_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        message = list(messages)[0].message
        assert response.context_data['favorite_locations'] == None
        assert response.context_data['location_history'] == None
        assert message['header'] == 'Location service error'
        assert message['search_results'] == None


class TestRandomLocation(TestCase):
    # Location API docs:
    # https://openrouteservice.org/dev/#/api-docs/geocode/reverse/get

    def test_show_random_location(self):
        url = reverse('random_location')
        params = {'display_mode': '7d_detail'}
        response = Client().get(url, params)
        assert response.status_code == 302
        redirect_uri = urlparse(response.url)
        assert redirect_uri.path == reverse('dashboard')
        redirect_params = parse_qs(redirect_uri.query)
        location_label = redirect_params['label'][0]
        assert not location_label in ['', None]
        location_latitude = float(redirect_params['latitude'][0])
        assert -90.0 <= location_latitude <= 90.0
        location_longitude = float(redirect_params['longitude'][0])
        assert -180.0 <= location_longitude <= 180.0
        assert params['display_mode'] == redirect_params['display_mode'][0]

    def test_show_random_location_with_ORS_timeout(self):
        request = RequestFactory().get(reverse('random_location'))
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = random_location(request, ORS_timeout=0.0001)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert response.context_data['favorite_locations'] == None
        assert response.context_data['location_history'] == None
        message = list(messages)[0].message
        assert message['header'] == 'Location service time out'

    def test_show_random_location_with_ORS_http_error(self):
        request = RequestFactory().get(reverse('random_location'))
        request.user = AnonymousUser()
        # Add session to request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Add messages to request
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = random_location(request, ORS_key='bad_key')
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/messages.html'):
            response.render()
        assert response.context_data['favorite_locations'] == None
        assert response.context_data['location_history'] == None
        message = list(messages)[0].message
        assert message['header'] == 'Location service error'


class TestUpdateLocation(TestCase):

    def test_add_favorite_location_with_login(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location = Location(
            **sample_location_params_1(),
            is_favorite=False,
            user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        url = reverse('update_location')
        params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'location_id': location.id,
            'is_favorite': True  # Add the location to favorites
        }
        redirect_params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude
        }
        response = client.post(url, params)
        updated_location = Location.objects.get(pk=location.id)
        assert updated_location.is_favorite  # Location updated successfully
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_params)}"
        self.assertRedirects(response, redirect_uri)

    def test_remove_favorite_location_with_login(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location = Location(
            **sample_location_params_1(),
            is_favorite=True,
            user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        url = reverse('update_location')
        params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'location_id': location.id,
            'is_favorite': False  # Remove the location from favorites
        }
        redirect_params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude
        }
        response = client.post(url, params)
        updated_location = Location.objects.get(pk=location.id)
        assert updated_location.is_favorite == False  # Location updated successfully
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_params)}"
        self.assertRedirects(response, redirect_uri)

    def test_add_favorite_location_without_location_id(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location = Location(
            **sample_location_params_1(),
            is_favorite=False,
            user=user)
        location.save()
        client = Client()
        client.login(**credentials)
        url = reverse('update_location')
        params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude,
            # MISSING 'location_id': location.id,
            'is_favorite': True  # Try to add the location to favorites
        }
        redirect_params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude
        }
        response = client.post(url, params)
        updated_location = Location.objects.get(pk=location.id)
        assert updated_location.is_favorite == False  # Location NOT updated
        redirect_uri = f"{reverse('dashboard')}?{urlencode(redirect_params)}"
        self.assertRedirects(response, redirect_uri)

    def test_add_favorite_location_without_login(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location_params = sample_location_params_1()
        location = Location(**location_params, user=user)
        location.is_favorite = True
        location.save()
        params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'location_id': location.id,
            'is_favorite': False  # Try to remove the location from favorites
        }
        update_url = reverse('update_location')
        login_url = reverse('login_user')
        response = Client().post(update_url, params)
        self.assertRedirects(
            response,
            f"{login_url}?next_url={update_url}")
        updated_location = Location.objects.get(pk=location.id)
        assert updated_location.is_favorite == True  # Location NOT updated
        assert login_url == settings.LOGIN_URL

    def test_remove_favorite_location_without_login(self):
        credentials = sample_credentials()
        user = User.objects.create_user(**credentials)
        location_params = sample_location_params_1()
        location = Location(**location_params, user=user)
        location.is_favorite = False
        location.save()
        params = {
            'display_mode': '7d_detail',
            'label': location.label,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'location_id': location.id,
            'is_favorite': True  # Try to add the location to favorites
        }
        update_url = reverse('update_location')
        login_url = reverse('login_user')
        response = Client().post(update_url, params)
        self.assertRedirects(
            response,
            f"{login_url}?next_url={update_url}")
        updated_location = Location.objects.get(pk=location.id)
        assert updated_location.is_favorite == False  # Location NOT updated
        assert login_url == settings.LOGIN_URL


class TestRegisterUser(TestCase):

    def test_show_user_registration_page_with_query(self):
        url = reverse('register_user')
        location_params = sample_location_params_1()
        display_mode = '7d_detail'
        query = {
            **location_params,
            'display_mode': display_mode}
        response = Client().get(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['location'] == location_params
        assert response.context['display_mode'] == display_mode

    def test_show_user_registration_page_without_query(self):
        url = reverse('register_user')
        response = Client().get(url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['location'] == {}
        assert response.context['display_mode'] == display_modes()[0]

    def test_register_new_user_with_unmatched_passwords(self):
        url = reverse('register_user')
        display_mode = display_modes()[0]
        location_params = sample_location_params_1()
        credentials = {
            'username': 'new user',
            'password1': '123456',
            'password2': '123456789'}
        query = {
            **credentials,
            **location_params,
            'display_mode': display_mode}
        client = Client()
        response = client.post(url, query)
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert not auth.get_user(client).is_authenticated
        assert response.context['error_message'] == 'Passwords do not match.'
        assert response.context['location'] == location_params
        assert response.context['display_mode'] == display_mode

    def test_register_existing_user(self):
        url = reverse('register_user')
        display_mode = display_modes()[0]
        location_params = sample_location_params_1()
        User.objects.create_user(
            username='new user',
            password='123456')
        credentials = {
            'username': 'new user',
            'password1': '123456',
            'password2': '123456'}
        query = {
            **credentials,
            **location_params,
            'display_mode': display_mode}
        client = Client()
        response = client.post(url, {**location_params, **credentials})
        assert response.status_code == 200
        self.assertTemplateUsed(response, 'weather_app/register_user.html')
        assert response.context['error_message'] == 'User already exists. Please choose different username.'
        assert response.context['location'] == location_params
        assert response.context['display_mode'] == display_mode

    def test_register_new_user(self):
        url = reverse('register_user')
        display_mode = display_modes()[0]
        location_params = sample_location_params_1()
        credentials = {
            'username': 'new user',
            'password1': '123456',
            'password2': '123456'}
        query = {
            **credentials,
            **location_params,
            'display_mode': display_mode}
        redirect_query = {
            **location_params,
            'display_mode': display_mode}
        redirect_base_url = reverse('dashboard')
        redirect_query_string = urlencode(redirect_query)
        redirect_uri = f"{redirect_base_url}?{redirect_query_string}"
        client = Client()
        response = client.post(url, query)
        self.assertRedirects(response, redirect_uri)
        assert auth.get_user(client).is_authenticated


class TestLoginUser(TestCase):

    def test_login_page_with_query(self):
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

    def test_login_page_without_query(self):
        url = reverse('login_user')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = login_user(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/login_user.html'):
            response.render()
        assert response.context_data['location'] == {}
        assert response.context_data['next_url'] == None

    def test_login_user_with_correct_credentials_without_query(self):
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

    def test_login_user_with_bad_credentials_without_query(self):
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

    def test_logout_without_query(self):
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

    def test_show_user_profile_without_login(self):
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

    def test_get_location_params_from_GET_without_query(self):
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        assert get_location_params(request) == {}

    def test_get_location_params_from_POST_with_query(self):
        url = reverse('dashboard')
        location_params = sample_location_params_1()
        request = RequestFactory().post(url, location_params)
        assert get_location_params(request) == location_params

    def test_get_location_params_from_POST_without_query(self):
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

    def test_get_location_history_without_login(self):
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

    def test_get_favorite_locations_without_login(self):
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

    # def test_redirect_to_dashboard_without_query(self):
    #     # https://docs.djangoproject.com/en/3.2/ref/request-response/
    #     response = redirect_to_dashboard()
    #     assert response.status_code == 302
    #     assert response.url == reverse('dashboard')

    def test_render_dashboard_without_query_without_login(self):
        url = reverse('dashboard')
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = render_dashboard(request)
        assert response.status_code == 200
        with self.assertTemplateUsed('weather_app/no_location.html'):
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
