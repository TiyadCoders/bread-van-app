import unittest
import datetime as dt
from unittest.mock import Mock, patch

from App.models.stop import Stop


class TestStop(unittest.TestCase):
    def setUp(self):
        self.driver = Mock()
        self.driver.id = 1
        self.driver.get_fullname.return_value = "John Driver"

        self.street = Mock()
        self.street.name = "Test Street"

        self.scheduled_date = "2024-01-15T10:00:00"

    @patch("App.models.stop.db")
    def test_create_stop(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )

        self.assertEqual(stop.driver_id, 1)
        self.assertEqual(stop.street_name, "Test Street")
        self.assertEqual(stop.scheduled_date, self.scheduled_date)
        self.assertFalse(stop.has_arrived)
        self.assertIsNotNone(stop.created_at)

    @patch("App.models.stop.db")
    def test_get_json_has_fields(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )
        stop.id = 1

        data = stop.get_json()

        self.assertIn("id", data)
        self.assertIn("driverId", data)
        self.assertIn("streetName", data)
        self.assertIn("scheduledDate", data)
        self.assertIn("createdAt", data)
        self.assertIn("hasArrived", data)

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["driverId"], 1)
        self.assertEqual(data["streetName"], "Test Street")
        self.assertEqual(data["scheduledDate"], self.scheduled_date)
        self.assertFalse(data["hasArrived"])

    @patch("App.models.stop.db")
    def test_to_api_dict_scheduled(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )
        stop.id = 1

        d = stop.to_api_dict()

        self.assertIn("id", d)
        self.assertIn("driverId", d)
        self.assertIn("driver", d)
        self.assertIn("streetName", d)
        self.assertIn("scheduledDate", d)
        self.assertIn("createdAt", d)
        self.assertIn("hasArrived", d)
        self.assertIn("status", d)

        self.assertEqual(d["status"], "scheduled")
        self.assertIsNone(d["driver"])  # no relationship loaded

    @patch("App.models.stop.db")
    def test_to_api_dict_completed(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )
        stop.has_arrived = True

        d = stop.to_api_dict()
        self.assertEqual(d["status"], "completed")

    @patch("App.models.stop.db")
    def test_complete(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )

        ok = stop.complete()
        self.assertTrue(ok)
        self.assertTrue(stop.has_arrived)

    @patch("App.models.stop.db")
    def test_complete_twice_returns_false(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )
        stop.has_arrived = True

        ok = stop.complete()
        self.assertFalse(ok)

    @patch("App.models.stop.db")
    def test_mark_arrival(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )

        ok = stop.mark_arrival()
        self.assertTrue(ok)
        self.assertTrue(stop.has_arrived)

    @patch("App.models.stop.db")
    def test_complete_handles_db_error(self, db):
        db.session.commit.side_effect = Exception("Database error")

        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )

        ok = stop.complete()
        self.assertFalse(ok)
        db.session.rollback.assert_called_once()

    @patch("App.models.stop.db")
    def test_created_at_is_iso(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )
        # just check it parses
        dt.datetime.fromisoformat(stop.created_at)

    @patch("App.models.stop.db")
    def test_to_string_changes_with_status(self, db):
        stop = Stop(
            driver=self.driver,
            street=self.street,
            scheduled_date=self.scheduled_date
        )

        s1 = stop.to_string()
        self.assertIn("Test Street", s1)
        self.assertIn("scheduled", s1)
        self.assertIn(self.scheduled_date, s1)

        stop.has_arrived = True
        s2 = stop.to_string()
        self.assertIn("Test Street", s2)
        self.assertIn("was made", s2)
        self.assertIn(self.scheduled_date, s2)


if __name__ == "__main__":
    unittest.main()
