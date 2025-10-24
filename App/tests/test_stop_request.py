import unittest
import datetime as dt
from unittest.mock import Mock, patch


from App.models.stop_request import StopRequest


class TestStopRequest(unittest.TestCase):
    def setUp(self):
        self.resident = Mock()
        self.resident.id = 1
        self.resident.street_name = "Sample Street"

    @patch("App.models.stop_request.db")
    def test_create_stop_request(self, db):
        stop_request = StopRequest(resident=self.resident)

        self.assertEqual(stop_request.resident_id, 1)
        self.assertEqual(stop_request.street_name, "Sample Street")
        self.assertIsNotNone(stop_request.created_at)

    @patch("App.models.stop_request.db")
    def test_get_json_has_fields(self, db):
        stop_request = StopRequest(resident=self.resident)
        stop_request.id = 1

        data = stop_request.get_json()

        self.assertIn("id", data)
        self.assertIn("resident_id", data)
        self.assertIn("street_name", data)
        self.assertIn("created_at", data)

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["resident_id"], 1)
        self.assertEqual(data["street_name"], "Sample Street")