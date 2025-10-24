import unittest
import datetime as dt
from unittest.mock import Mock, patch

from App.models.street import Street

class TestStreet(unittest.TestCase):
    def setUp(self):
        self.created_at = dt.datetime(2024, 1, 1, 12, 0, 0)

    @patch("App.models.street.db")
    def test_street_creation(self, db):
        street = Street(name="Main St")
        self.assertEqual(street.name, "Main St")
    
    @patch("App.models.street.db")
    def test_get_json(self, db):
        street = Street(name="Main St")
        expected_json = {
            'name': "Main St"
        }
        self.assertEqual(street.get_json(), expected_json)

        







    
        

