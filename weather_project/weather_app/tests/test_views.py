from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, Client, RequestFactory
from weather_app.views import *
from datetime import datetime
import pytz
import copy
from django.urls import reverse
from urllib.parse import urlencode
from django.test import RequestFactory
import json
import pickle
from weather_app.models import User, Location


class TestUtils(TestCase):
    def setUp(self):
        with open('weather_app/tests/sample_data/weather.pkl', 'rb') as file:
            self.sample_weather = pickle.load(file)
        with open('weather_app/tests/sample_data/air_pollution.pkl', 'rb') as file:
            self.sample_air_pollution = pickle.load(file)
        with open('weather_app/tests/sample_data/charts.pkl', 'rb') as file:
            self.sample_charts = pickle.load(file)
        with open('weather_app/tests/sample_data/location_history.pkl', 'rb') as file:
            self.sample_location_history = pickle.load(file)
        with open('weather_app/tests/sample_data/favorite_locations.pkl', 'rb') as file:
            self.sample_favorite_locations = pickle.load(file)
        self.sample_user = User.objects.create_user(
            username='John',
            password='123456')
        self.sample_location = Location(
            latitude=-16.36667,
            longitude=-58.4,
            label='San Matías, SC, Bolivia',
            user=self.sample_user)
        self.sample_location.save()
        self.sample_timezone = pytz.timezone('America/La_Paz')

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

    def test_redirect_to_dashboard_without_params(self):
        # https://docs.djangoproject.com/en/3.2/ref/request-response/
        response = redirect_to_dashboard()
        assert response.status_code == 302
        assert response.url == reverse('dashboard')

    def test_redirect_to_dashboard_with_location_params(self):
        base_url = reverse('dashboard')
        location_params = {
            'latitude': 30,
            'longitude': 40,
            'label': 'Test Location'}
        query_string = urlencode(location_params)
        uri = f'{base_url}?{query_string}'
        response = redirect_to_dashboard(location_params)
        assert response.status_code == 302
        assert response.url == uri

    def test_render_dashboard_without_params(self):
        # https://docs.djangoproject.com/en/3.2/ref/request-response/
        # https://docs.djangoproject.com/en/3.2/topics/testing/advanced/#the-request-factory
        factory = RequestFactory()
        request = factory.get(reverse('dashboard'))
        request.user = AnonymousUser()
        response = render_dashboard(request)
        assert response.status_code == 200

    def test_render_dashboard_with_params(self):
        factory = RequestFactory()
        request = factory.get(reverse('dashboard'))
        request.user = AnonymousUser()
        response = render_dashboard(
            request,
            location=self.sample_location,
            weather=self.sample_weather,
            air_pollution=self.sample_air_pollution,
            charts=self.sample_charts)
        assert response.status_code == 200

    def test_get_charts(self):
        assert get_charts(self.sample_weather) == self.sample_charts          
        
