from django.test import TestCase
from weather_app.models import User, Location
from django.core.exceptions import ValidationError


class TestLocation(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='123456')
        self.location = Location(
            latitude=30,
            longitude=40,
            label='Test Location',
            user=self.user)

    def test_create_location(self):
        self.assertIsInstance(self.location, Location)

    def test_str_representation(self):
        assert str(self.location) == 'Test Location'

    def test_location_label_bad_values(self):
        bad_values = [None, '']
        for bad_one in bad_values:
            # https://docs.python.org/3/library/unittest.html#subtests
            with self.subTest(bad_one=bad_one):
                self.location.label = bad_one
                self.assertRaises(ValidationError, self.location.clean_fields)

    def test_location_latitude_limit_values(self):
        limit_values = [-90, 90]
        for limit in limit_values:
            with self.subTest(limit=limit):
                self.location.latitude = limit
                self.location.clean_fields()

    def test_location_latitude_bad_values(self):
        bad_values = [-90.1, 90.1, None, '']
        for bad_one in bad_values:
            with self.subTest(bad_one=bad_one):
                self.location.latitude = bad_one
                self.assertRaises(ValidationError, self.location.clean_fields)

    def test_location_longitude_limit_values(self):
        limit_values = [-180, 180]
        for limit in limit_values:
            with self.subTest(limit=limit):
                self.location.longitude = limit
                self.location.clean_fields()

    def test_location_longitude_bad_values(self):
        bad_values = [-180.1, 180.1, None, '']
        for bad_one in bad_values:
            with self.subTest(bad_one=bad_one):
                self.location.longitude = bad_one
                self.assertRaises(ValidationError, self.location.clean_fields)
