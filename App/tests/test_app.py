import os, tempfile, pytest, logging, unittest, io
from werkzeug.security import check_password_hash, generate_password_hash
from contextlib import redirect_stdout
from datetime import datetime, timedelta

from App.main import create_app
from App.extensions import db
from App.database import create_db
from App.models import User
from App.models.enums import NotificationType 
from App.controllers.user import (
    create_user,
    create_resident,
    get_all_users_json,
    get_user_by_id,
    create_driver,
    get_driver_by_id,
    get_all_drivers_json

)
from App.controllers.street import (
    create_street,
    get_street_by_string,
    get_all_streets_json
)
from App.controllers.stop import (
    create_stop,
    get_all_stops,
    get_stop_by_id,
    delete_stop,
    complete_stop,
    stop_exists
)
from App.controllers.notification import (
    create_notification,
    create_street_notification,
    create_user_notification,
    create_system_notification,
    get_notifications_by_street,
    get_notifications_by_user,
    get_notifications_by_type,
    get_unread_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,


)
from App.controllers.auth import login


LOGGER = logging.getLogger(__name__)

'''
    Integration Tests
'''

# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    create_db()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = create_user("bob", "bobpass", "Bob", "Builder")
    assert login("bob", "bobpass") != None

class ResidentIntegrationTests(unittest.TestCase):

     def test_create_resident(self):
         street = create_street("Main St")
         user = create_resident("res1", "respass", "Res", "Ident", street)
         get_user_by_id(user.id)
         self.assertIsNotNone(user)

     def test_get_all_users_json(self):
        user1 = create_user("user1", "pass1", "User", "One")
        user2 = create_user("user2", "pass2", "User", "Two")
        users_json = get_all_users_json()
        self.assertIsInstance(users_json, list)
        self.assertGreaterEqual(len(users_json), 2)

class ResidentIntegrationTests(unittest.TestCase):

     def test_create_resident(self):
         street = create_street("Main St")
         user = create_resident("res1", "respass", "Res", "Ident", street)
         get_user_by_id(user.id)
         self.assertIsNotNone(user)

     def test_get_all_users_json(self):
        user1 = create_user("user1", "pass1", "User", "One")
        user2 = create_user("user2", "pass2", "User", "Two")
        users_json = get_all_users_json()
        self.assertIsInstance(users_json, list)
        self.assertGreaterEqual(len(users_json), 2)

     def test_create_notifications(self):
        street_name = "Inbox Ave"
        street = create_street(street_name) or get_street_by_string(street_name)
        user = create_resident("inbox_res", "inbox_pass", "In", "Box", street)

        n_user = create_user_notification(
            "User Alert", "User-specific notice.", user,
            notification_type=NotificationType.REQUESTED
        )
        n_street = create_street_notification(
            "Street Alert", "Street-level notice.", street,
            notification_type=NotificationType.CONFIRMED
        )
        n_system = create_system_notification("System Alert", "System-wide notice.")

        self.assertIsNotNone(n_user)
        self.assertIsNotNone(n_street)
        self.assertIsNotNone(n_system)

        buf = io.StringIO()
        with redirect_stdout(buf):
            user.view_inbox("all")
        out = buf.getvalue()

        self.assertTrue(out and "Inbox is empty." not in out)

        self.assertIn("User-specific notice.", out)
        self.assertIn("Street-level notice.", out)

class DriverIntegrationTests(unittest.TestCase):

     def test_create_driver(self):
         user = create_user("driver1", "driverpass", "Driver", "Ident")
         get_user_by_id(user.id)
         self.assertIsNotNone(user)

     def test_get_all_drivers_json(self):
        user1 = create_driver("user3", "pass3", "User", "Three")
        user2 = create_driver("user4", "pass4", "User", "Four ")
        drivers = get_all_drivers_json()
        self.assertIsInstance(drivers, list)
        self.assertGreaterEqual(len(drivers), 2)


class StreetIntegrationTests(unittest.TestCase):

     def test_create_street(self):
         street = create_street("Elm St")
         fetched_street = get_street_by_string("Elm St")
         self.assertIsNotNone(street)
         self.assertEqual(street.name, fetched_street.name)

     def test_get_all_streets_json(self):
        street1 = create_street("Pine St")
        street2 = create_street("Oak St")
        streets = get_all_streets_json()
        self.assertIsInstance(streets, list)
        self.assertGreaterEqual(len(streets), 2)


class StopIntegrationTests(unittest.TestCase):

     def test_create_stop(self):
         driver = create_driver("driver2", "driverpass2", "Driver", "Two")
         street = create_street("Maple St")
         stop = create_stop(driver=driver, street=street, scheduled_date="2024-10-01")
         self.assertIsNotNone(stop)

     def test_get_all_stops(self):
        driver = create_driver("driver3", "driverpass3", "Driver", "Three")
        street1 = create_street("Birch St")
        street2 = create_street("Cedar St")
        stop1 = create_stop(driver=driver, street=street1, scheduled_date="2024-11-01")
        stop2 = create_stop(driver=driver, street=street2, scheduled_date="2024-11-02")
        stops = get_all_stops()
        self.assertIsInstance(stops, list)
        self.assertGreaterEqual(len(stops), 2)

     def test_complete_stop(self):
        driver = create_driver("driver4", "driverpass4", "Driver", "Four")
        street = create_street("Spruce St")
        stop = create_stop(driver=driver, street=street, scheduled_date="2024-12-01")
        complete_stop(stop.id)
        fetched_stop = get_stop_by_id(stop.id)
        self.assertTrue(fetched_stop.has_arrived)

     def test_delete_stop(self):
        driver = create_driver("driver5", "driverpass5", "Driver", "Five")
        street = create_street("Willow St")
        stop = create_stop(driver=driver, street=street, scheduled_date="2025-01-01")
        delete_stop(stop.id)
        fetched_stop = get_stop_by_id(stop.id)
        self.assertIsNone(fetched_stop)

     def test_stop_exists(self):
        
        driver = create_driver("driver_exists_it1", "driverpass_exists", "Driver", "Exists")

        street_name = "Spruce St"  
        street = create_street(street_name)
        if street is None:
            street = get_street_by_string(street_name)
        self.assertIsNotNone(street)

        date = "2025-02-01"

        self.assertFalse(stop_exists(street.name, date))

        stop = create_stop(driver=driver, street=street, scheduled_date=date)
        self.assertIsNotNone(stop)

        self.assertTrue(stop_exists(street.name, date))
        self.assertFalse(stop_exists("Nonexistent St", date))
        self.assertFalse(stop_exists(street.name, "2099-01-01"))
 

class NotificationIntegrationTests(unittest.TestCase):

        def test_create_and_fetch_street_notification(self):
            street = create_street("Chestnut St")
            notification = create_street_notification("Street Alert", "This is a street alert.", street)
            fetched_notifications = get_notifications_by_street(street)
            self.assertIn(notification, fetched_notifications)

        def test_create_user_notification_appears_in_unread_count(self):
            user = create_user("unread_user_ix1", "pass", "Un", "Read")
            self.assertIsNotNone(user)

            baseline = get_unread_count(user, include_global=True)
            self.assertIsInstance(baseline, int)

            notif = create_user_notification(
                title="Unread Ping",
                message="Please check this.",
                recipient=user,
            )
            self.assertIsNotNone(notif)

            after = get_unread_count(user, include_global=True)
            self.assertEqual(after, baseline + 1)

        def test_create_and_mark_user_notification_as_read(self):
            user = create_user("mark_read_user_ix1", "pass", "Mark", "Read")
            self.assertIsNotNone(user)

            baseline = get_unread_count(user, include_global=True)
            self.assertIsInstance(baseline, int)

            notif = create_user_notification(
                title="Mark Me",
                message="This will be marked as read.",
                recipient=user,
            )
            self.assertIsNotNone(notif)
            self.assertIsNotNone(getattr(notif, "id", None))

            after_create = get_unread_count(user, include_global=True)
            self.assertEqual(after_create, baseline + 1)

            marked = mark_notification_as_read(notif.id, user=user)
            self.assertTrue(marked, "mark_notification_as_read returned False")

            after_read = get_unread_count(user, include_global=True)
            self.assertEqual(after_read, baseline)

        def test_create_and_fetch_user_notification(self):
            user = create_user("user5", "pass5", "User", "Five")
            notification = create_user_notification("User Alert", "This is a user alert.", user)
            fetched_notifications = get_notifications_by_user(user)
            self.assertIn(notification, fetched_notifications)

        def test_create_and_fetch_system_notification(self):
            notification = create_system_notification("System Alert", "This is a system alert.")
            fetched_notifications = get_notifications_by_type("system")
            self.assertIn(notification, fetched_notifications)

        def test_get_unread_count_and_mark_as_read(self):
            user = create_user("user6", "pass6", "User", "Six")
            # Get initial count
            initial_count = get_unread_count(user)
            # Create a notification
            notification = create_user_notification("Unread Alert", "This is an unread alert.", user)
            # Count should increase by 1
            unread_count = get_unread_count(user)
            self.assertEqual(unread_count, initial_count + 1)
            # Mark as read
            mark_notification_as_read(notification.id, user)
            # Count should decrease by 1
            unread_count_after = get_unread_count(user)
            self.assertEqual(unread_count_after, initial_count)

        def test_create_street_notification_with_type_filter(self):
            street_name = "Filter Ave"
            street = create_street(street_name) or get_street_by_string(street_name)
            self.assertIsNotNone(street)

            title = "Schedule Drop"
            msg = "Collection schedule updated."
            notif = create_street_notification(
                title=title,
                message=msg,
                street=street,
                notification_type=NotificationType.SCHEDULE,
            )
            self.assertIsNotNone(notif)

            results = get_notifications_by_type(NotificationType.SCHEDULE, street=street)
            self.assertIsInstance(results, list)
            self.assertGreaterEqual(len(results), 1)
            self.assertIn(title, {getattr(n, "title", None) for n in results})

            other = get_notifications_by_type(NotificationType.CONFIRMED, street=street)
            self.assertIsInstance(other, list)
            self.assertNotIn(title, {getattr(n, "title", None) for n in other})
        
        def test_create_system_notification_appears_for_all_users(self):
            u1 = create_user("sys_user_a_ix1", "pass", "Sys", "A")
            u2 = create_user("sys_user_b_ix1", "pass", "Sys", "B")
            self.assertIsNotNone(u1)
            self.assertIsNotNone(u2)

            title = "Global Broadcast IX1"
            msg = "This message is for everyone."
            notif = create_system_notification(title=title, message=msg)
            self.assertIsNotNone(notif)

            for user in (u1, u2):
                items = get_notifications_by_user(user, include_global=True, unread_only=False, limit=200)
                self.assertIsInstance(items, list)
                titles = {getattr(n, "title", None) for n in items}
                self.assertIn(title, titles, f"System notification not visible for user {user.username}")
        
        def test_user_receives_personal_and_street_notifications(self):
            street_name = "Both Ave"
            street = create_street(street_name) or get_street_by_string(street_name)
            user = create_resident("both_user_ix1", "pass", "Both", "Case", street)
            self.assertIsNotNone(user)

            personal_title = "Personal Ping"
            street_title = "Street Ping"

            n_user = create_user_notification(
                title=personal_title,
                message="Direct to you.",
                recipient=user,
            )
            self.assertIsNotNone(n_user)

            n_street = create_street_notification(
                title=street_title,
                message="FYI for your street.",
                street=street,
            )
            self.assertIsNotNone(n_street)

            items = get_notifications_by_user(user, include_global=True, unread_only=False, limit=200)
            self.assertIsInstance(items, list)
            titles = {getattr(n, "title", None) for n in items}

            self.assertIn(personal_title, titles, "Personal notification missing from user's list")
            self.assertIn(street_title, titles, "Street notification missing from user's list")

        def test_user_cannot_mark_other_users_notification(self):
            user_a = create_user("owner_ix1", "pass", "Own", "Er")
            user_b = create_user("intruder_ix1", "pass", "Intru", "Der")
            self.assertIsNotNone(user_a)
            self.assertIsNotNone(user_b)

            notif = create_user_notification(
                title="Private Msg",
                message="For A only.",
                recipient=user_a,
            )
            self.assertIsNotNone(notif)
            self.assertIsNotNone(getattr(notif, "id", None))

            denied = mark_notification_as_read(notif.id, user=user_b)

            self.assertFalse(denied, "Non-owner was able to mark another user's notification as read")

            allowed = mark_notification_as_read(notif.id, user=user_a)
            self.assertTrue(allowed, "Owner could not mark their own notification as read")

        def test_street_and_user_notifications_ordered_correctly(self):
            street_name = "Order Ave"
            street = create_street(street_name) or get_street_by_string(street_name)
            user = create_resident("order_user_ix1", "pass", "Or", "Der", street)
            self.assertIsNotNone(user)

            n_old = create_user_notification("Old Personal", "old msg", user)
            n_mid = create_street_notification("Middle Street", "mid msg", street)
            n_new = create_user_notification("Newest Personal", "new msg", user)
            self.assertIsNotNone(n_old)
            self.assertIsNotNone(n_mid)
            self.assertIsNotNone(n_new)

            now = datetime.utcnow()
            n_new.created_at = now - timedelta(seconds=1)
            n_mid.created_at = now - timedelta(seconds=60)
            n_old.created_at = now - timedelta(seconds=120)
            db.session.add_all([n_new, n_mid, n_old])
            db.session.commit()

            items = get_notifications_by_user(user, include_global=True, unread_only=False, limit=50)
            self.assertIsInstance(items, list)

            target_titles = {"Old Personal", "Middle Street", "Newest Personal"}
            ordered_seen = [getattr(i, "title", None) for i in items if getattr(i, "title", None) in target_titles]

            self.assertGreaterEqual(len(ordered_seen), 3)
            self.assertEqual(ordered_seen[:3], ["Newest Personal", "Middle Street", "Old Personal"])
        


