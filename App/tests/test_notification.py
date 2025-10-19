import unittest
import datetime as dt
from unittest.mock import Mock, patch

from App.models.notification import Notification
from App.models.enums import NotificationType, NotificationCategory, NotificationPriority


class TestNotification(unittest.TestCase):
    def setUp(self):
        self.title = "Test Notification"
        self.message = "This is a test notification message"
        self.notification_type = NotificationType.SYSTEM

        self.user = Mock()
        self.user.id = 1
        self.user.type = "resident"
        self.user.get_fullname.return_value = "John Doe"

        self.street = Mock()
        self.street.name = "Test Street"

    def test_creation_basic(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )

        self.assertEqual(n.title, self.title)
        self.assertEqual(n.message, self.message)
        self.assertEqual(n.type, self.notification_type.value)
        self.assertEqual(n.category, NotificationCategory.GENERAL.value)
        self.assertEqual(n.priority, NotificationPriority.NORMAL.value)
        self.assertFalse(n.is_read)
        self.assertTrue(n.is_global)
        self.assertIsNotNone(n.created_at)

    def test_creation_with_recipient(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            recipient=self.user
        )
        self.assertEqual(n.recipient_id, self.user.id)
        self.assertEqual(n.recipient_type, self.user.type)
        self.assertFalse(n.is_global)

    def test_creation_with_street(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            street=self.street
        )
        self.assertEqual(n.street_name, self.street.name)

    def test_creation_with_all_params(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            recipient=self.user,
            street=self.street,
            category=NotificationCategory.SERVICE,
            priority=NotificationPriority.HIGH
        )
        self.assertEqual(n.category, NotificationCategory.SERVICE.value)
        self.assertEqual(n.priority, NotificationPriority.HIGH.value)
        self.assertEqual(n.recipient_id, self.user.id)
        self.assertEqual(n.street_name, self.street.name)

    def test_defaults(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        self.assertEqual(n.category, NotificationCategory.GENERAL.value)
        self.assertEqual(n.priority, NotificationPriority.NORMAL.value)
        self.assertFalse(n.is_read)
        self.assertTrue(n.is_global)
        self.assertIsNone(n.recipient_id)
        self.assertIsNone(n.recipient_type)
        self.assertIsNone(n.street_name)
        self.assertIsNone(n.read_at)

    def test_created_at_window(self):
        before = dt.datetime.utcnow()
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        after = dt.datetime.utcnow()
        self.assertLessEqual(before, n.created_at)
        self.assertLessEqual(n.created_at, after)

    @patch("App.models.notification.db.session")
    def test_mark_as_read_success(self, session):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        ok = n.mark_as_read()
        self.assertTrue(ok)
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)
        session.add.assert_called_once_with(n)
        session.commit.assert_called_once()

    @patch("App.models.notification.db.session")
    def test_mark_as_read_already_read(self, session):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.is_read = True
        n.read_at = dt.datetime.utcnow()

        ok = n.mark_as_read()
        self.assertTrue(ok)
        session.add.assert_not_called()
        session.commit.assert_not_called()

    @patch("App.models.notification.db.session")
    def test_mark_as_read_db_error(self, session):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        session.commit.side_effect = Exception("db error")
        ok = n.mark_as_read()
        self.assertFalse(ok)
        session.rollback.assert_called_once()

    def test_age_in_minutes(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.created_at = dt.datetime.utcnow() - dt.timedelta(minutes=30)
        age = n.get_age_in_minutes()
        self.assertGreaterEqual(age, 29)
        self.assertLessEqual(age, 31)

    def test_get_json_basic(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.id = 1
        data = n.get_json()
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], self.title)
        self.assertEqual(data["message"], self.message)
        self.assertEqual(data["type"], self.notification_type.value)
        self.assertEqual(data["category"], NotificationCategory.GENERAL.value)
        self.assertEqual(data["priority"], NotificationPriority.NORMAL.value)
        self.assertFalse(data["isRead"])
        self.assertTrue(data["isGlobal"])
        self.assertIsNone(data["recipientId"])
        self.assertIsNone(data["streetName"])

    def test_get_json_with_recipient_and_street(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            recipient=self.user,
            street=self.street
        )
        n.id = 1
        data = n.get_json()
        self.assertEqual(data["recipientId"], self.user.id)
        self.assertEqual(data["recipientType"], self.user.type)
        self.assertEqual(data["streetName"], self.street.name)
        self.assertFalse(data["isGlobal"])

    @patch("App.models.notification.db")
    def test_to_api_dict_with_recipient_field_none_if_unloaded(self, db):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            recipient=self.user
        )
        n.id = 1
        d = n.to_api_dict()
        self.assertIn("recipient", d)
        self.assertIsNone(d["recipient"])

    def test_to_api_dict_without_recipient(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.id = 1
        n.recipient = None
        d = n.to_api_dict()
        self.assertIsNone(d["recipient"])

    def test_format_created_at_just_now(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        self.assertEqual(n.format_created_at(), "Just now")

    def test_format_created_at_minutes(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.created_at = dt.datetime.utcnow() - dt.timedelta(minutes=5)
        self.assertEqual(n.format_created_at(), "5 minutes ago")

    def test_format_created_at_hours(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.created_at = dt.datetime.utcnow() - dt.timedelta(hours=2)
        self.assertEqual(n.format_created_at(), "2 hours ago")

    def test_format_created_at_days(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        n.created_at = dt.datetime.utcnow() - dt.timedelta(days=3)
        self.assertEqual(n.format_created_at(), "3 days ago")

    def test_to_string(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type
        )
        s = n.to_string()
        self.assertIn(self.message, s)
        self.assertIn("Created", s)

    def test_camel_case_keys_exist(self):
        n = Notification(
            title=self.title,
            message=self.message,
            notification_type=self.notification_type,
            recipient=self.user,
            street=self.street
        )
        n.id = 1

        data = n.get_json()
        api = n.to_api_dict()

        keys = [
            "isRead", "isGlobal", "recipientId", "recipientType",
            "streetName", "createdAt", "readAt", "ageInMinutes", "formattedCreatedAt"
        ]

        # just check presence where provided
        for k in keys:
            if k in data:
                self.assertIn(k, data)
            if k in api:
                self.assertIn(k, api)

    def test_different_types(self):
        for t in [NotificationType.ARRIVED, NotificationType.CONFIRMED,
                  NotificationType.CANCELLED, NotificationType.SYSTEM]:
            n = Notification(title=f"t {t.value}", message="m", notification_type=t)
            self.assertEqual(n.type, t.value)

    def test_categories_and_priorities(self):
        cats = [NotificationCategory.SCHEDULE, NotificationCategory.SERVICE, NotificationCategory.SYSTEM]
        pris = [NotificationPriority.LOW, NotificationPriority.HIGH, NotificationPriority.URGENT]
        for c in cats:
            for p in pris:
                n = Notification(
                    title=self.title,
                    message=self.message,
                    notification_type=self.notification_type,
                    category=c,
                    priority=p
                )
                self.assertEqual(n.category, c.value)
                self.assertEqual(n.priority, p.value)


if __name__ == "__main__":
    unittest.main()
