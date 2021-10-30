from django.test import TestCase, Client
from .models import Location
from django.core.exceptions import ValidationError


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



