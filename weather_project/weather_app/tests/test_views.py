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
from weather_app.models import User, Location


class TestUtils(TestCase):
    def setUp(self):
        pass
        self.sample_user = User.objects.create_user(
            username='John',
            password='123456')
        self.sample_location = Location(
            latitude=-6.532008,
            longitude=-64.39027,
            label= 'Canutama, AM, Brazil',
            user=self.sample_user)
        self.sample_location.save()
        self.sample_timezone = pytz.timezone('America/Manaus')
        with open('weather_app/tests/sample_weather.json', 'r') as file:
            self.sample_weather = json.load(file)
        with open('weather_app/tests/sample_air_pollution.json', 'r') as file:
            self.sample_air_pollution = json.load(file)
        with open('weather_app/tests/sample_location_history.json', 'r') as file:
            self.sample_location_history = json.load(file)
        with open('weather_app/tests/sample_favorite_locations.json', 'r') as file:
            self.sample_favorite_locations = json.load(file)

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
        url = reverse('dashboard')
        location_params = {
            'latitude': 30,
            'longitude': 40,
            'label': 'Test Location'}
        query_string = urlencode(location_params)
        uri = f'{url}?{query_string}'
        response = redirect_to_dashboard(location_params)
        assert response.status_code == 302
        assert response.url == uri

    def test_render_dashboard_without_params(self):
        # https://docs.djangoproject.com/en/3.2/ref/request-response/
        # https://docs.djangoproject.com/en/3.2/topics/testing/advanced/#the-request-factory
        factory = RequestFactory()
        request = factory.get('this_URL_does_not_matter')
        request.user = AnonymousUser()
        response = render_dashboard(request)
        assert response.status_code == 200        
