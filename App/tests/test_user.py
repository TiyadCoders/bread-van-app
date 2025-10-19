import unittest
from unittest.mock import Mock, patch

from App.models.user import User, Driver, Resident
from App.models.enums import DriverStatus


class TestUser(unittest.TestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass"
        self.first_name = "Test"
        self.last_name = "User"

    def test_user_creation(self):
        user = User(
            username=self.username,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name
        )

        self.assertEqual(user.username, self.username)
        self.assertEqual(user.first_name, self.first_name)
        self.assertEqual(user.last_name, self.last_name)
        self.assertEqual(user.type, "user")
        self.assertNotEqual(user.password, self.password)

    def test_set_password(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(len(user.password) > len(self.password))

    def test_check_password_valid(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        self.assertTrue(user.check_password(self.password))

    def test_check_password_invalid(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        self.assertFalse(user.check_password("wrongpassword"))

    def test_get_fullname(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        self.assertEqual(user.get_fullname(), f"{self.first_name} {self.last_name}")

    def test_get_json(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        user.id = 1
        data = user.get_json()

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["username"], self.username)
        self.assertEqual(data["firstName"], self.first_name)
        self.assertEqual(data["lastName"], self.last_name)
        self.assertEqual(data["type"], "user")

    def test_to_api_dict(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        user.id = 1
        d = user.to_api_dict()

        self.assertIn("id", d)
        self.assertIn("username", d)
        self.assertIn("firstName", d)
        self.assertIn("lastName", d)
        self.assertIn("fullName", d)
        self.assertEqual(d["fullName"], f"{self.first_name} {self.last_name}")

    def test_str(self):
        user = User(self.username, self.password, self.first_name, self.last_name)
        user.id = 1
        self.assertEqual(str(user), f"<User 1 {self.first_name} {self.last_name}>")


class TestDriver(unittest.TestCase):
    def setUp(self):
        self.username = "driver1"
        self.password = "driverpass"
        self.first_name = "John"
        self.last_name = "Driver"

    def test_driver_creation(self):
        driver = Driver(
            username=self.username,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name
        )

        self.assertEqual(driver.username, self.username)
        self.assertEqual(driver.type, "driver")
        self.assertEqual(driver.status, DriverStatus.INACTIVE.value)
        self.assertIsNone(driver.current_location)


    @patch("App.models.user.db.session")
    def test_update_status_valid(self, mock_session):
        driver = Driver(self.username, self.password, self.first_name, self.last_name)

        ok = driver.update_status("en_route", "Downtown")
        self.assertTrue(ok)
        self.assertEqual(driver.status, "en_route")
        self.assertEqual(driver.current_location, "Downtown")

        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    def test_update_status_invalid(self):
        driver = Driver(self.username, self.password, self.first_name, self.last_name)
        ok = driver.update_status("not_a_status", "Somewhere")
        self.assertFalse(ok)

    @patch("App.models.user.db.session")
    @patch("App.models.user.Stop")
    def test_schedule_stop_success(self, mock_stop_class, mock_session):
        driver = Driver(self.username, self.password, self.first_name, self.last_name)
        driver.id = 1

        street = Mock()
        street.name = "Test Street"

        mock_stop = Mock()
        mock_stop_class.return_value = mock_stop

        result = driver.schedule_stop(street, "2025-12-01")

        self.assertEqual(result, mock_stop)
        mock_stop_class.assert_called_once_with(driver, street, "2025-12-01")
        mock_session.add.assert_called_once_with(mock_stop)
        mock_session.commit.assert_called_once()

    @patch("App.models.user.db.session")
    @patch("App.models.user.Stop")
    def test_schedule_stop_failure(self, mock_stop_class, mock_session):
        driver = Driver(self.username, self.password, self.first_name, self.last_name)

        street = Mock()
        mock_stop = Mock()
        mock_stop_class.return_value = mock_stop

        from sqlalchemy.exc import SQLAlchemyError
        mock_session.commit.side_effect = SQLAlchemyError("db error")

        with patch("App.models.user.click.secho"):
            result = driver.schedule_stop(street, "2025-12-01")

        self.assertIsNone(result)
        mock_session.rollback.assert_called_once()

    def test_driver_get_json(self):
        driver = Driver(self.username, self.password, self.first_name, self.last_name)
        driver.id = 1
        driver.status = "en_route"
        driver.current_location = "Downtown"

        data = driver.get_json()
        self.assertEqual(data["type"], "driver")
        self.assertEqual(data["status"], "en_route")
        self.assertEqual(data["currentLocation"], "Downtown")

    def test_driver_to_api_dict(self):
        driver = Driver(self.username, self.password, self.first_name, self.last_name)
        driver.id = 1

        d = driver.to_api_dict()
        self.assertIn("status", d)
        self.assertIn("currentLocation", d)
        self.assertEqual(d["type"], "driver")


class TestResident(unittest.TestCase):
    def setUp(self):
        self.username = "resident1"
        self.password = "residentpass"
        self.first_name = "Jane"
        self.last_name = "Resident"
        self.street_name = "Elm Street"

    def test_resident_creation(self):
        resident = Resident(
            username=self.username,
            password=self.password,
            first_name=self.first_name,
            last_name=self.last_name,
            street_name=self.street_name
        )

        self.assertEqual(resident.username, self.username)
        self.assertEqual(resident.type, "resident")
        self.assertEqual(resident.street_name, self.street_name)

    @patch("App.models.user.db.session")
    @patch("App.models.user.StopRequest")
    def test_request_stop_basic(self, mock_stop_request_class, mock_session):
        resident = Resident(
            self.username, self.password, self.first_name, self.last_name, self.street_name
        )

        mock_stop_request = Mock()
        mock_stop_request_class.return_value = mock_stop_request

        # Only checking it can be called without blowing up
        self.assertTrue(hasattr(resident, "request_stop"))
        self.assertTrue(callable(resident.request_stop))

    def test_resident_get_json(self):
        resident = Resident(
            self.username, self.password, self.first_name, self.last_name, self.street_name
        )
        resident.id = 1

        data = resident.get_json()
        self.assertEqual(data["type"], "resident")
        self.assertEqual(data["streetName"], self.street_name)

    def test_resident_to_api_dict(self):
        resident = Resident(
            self.username, self.password, self.first_name, self.last_name, self.street_name
        )
        resident.id = 1

        d = resident.to_api_dict()
        self.assertIn("streetName", d)
        self.assertEqual(d["type"], "resident")
        self.assertEqual(d["streetName"], self.street_name)


if __name__ == "__main__":
    unittest.main()
