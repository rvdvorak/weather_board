from django.test import TestCase, Client
from .models import Location
from .views import *
from django.core.exceptions import ValidationError
from datetime import datetime
import pytz
import copy


class TestLocationModel(TestCase):
    def setUp(self):
        self.location = Location(
            latitude=30,
            longitude=40,
            label='Test Location')

    def test_create_location(self):
        self.assertIsInstance(self.location, Location)

    def test_str_representation(self):
        # self.assertEquals(str(self.location), 'Test Location')
        assert str(self.location) == 'Test Location'

    def test_validation(self):
        self.assertRaises(ValidationError, self.location.clean_fields)


class TestHomePage(TestCase):
    def setUp(self):
        client = Client()

    def test_home_page_status(self):
        response = self.client.get('/')
        assert response.status_code == 200


class TestUtils(TestCase):
    def setUp(self):
        pass

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