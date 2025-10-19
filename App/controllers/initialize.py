from .user import create_driver
from App.extensions import db
from .street import create_street
from .user import create_resident
from App.models import NotificationType
from App.models.enums import NotificationCategory, NotificationPriority
from .notification import create_street_notification, create_notification


def initialize():
    db.drop_all()
    db.create_all()

    streets_str = ['Randy Street', 'Author Street', 'Murray Drive', 'Charles Avenue']
    streets = [create_street(street) for street in streets_str]

    driver_1 = create_driver('bob', 'bobpass', 'Bob', 'Yi')
    driver_2 = create_driver('tuck', 'tuckpass', 'Tucker', 'Moore')
    create_resident('rick', 'rickpass', 'Rick', 'Smith', streets[0])
    create_resident('amy', 'amypass', 'Amy', 'Persad', streets[1])

    driver_1.update_status("en_route", "Laventille")
    driver_2.update_status("inactive", "Home")

    driver_1.schedule_stop(
        street=streets[0],
        date='2025-09-14'
    )
    create_street_notification(
        title="Stop Scheduled",
        message=f"A stop was successfully scheduled by '{driver_1.get_fullname()}' at street '{streets[0].name}' for '2025-09-14'.",
        street=streets[0],
        notification_type=NotificationType.CONFIRMED,
        category=NotificationCategory.SCHEDULE,
        priority=NotificationPriority.HIGH,
        expires_in_hours=168  # 1 week
    )

    driver_2.schedule_stop(
        street=streets[0],
        date='2025-09-20'
    )
    create_street_notification(
        title="Stop Scheduled",
        message=f"A stop was successfully scheduled by '{driver_2.get_fullname()}' at street '{streets[0].name}' for '2025-09-20'.",
        street=streets[0],
        notification_type=NotificationType.CONFIRMED,
        category=NotificationCategory.SCHEDULE,
        priority=NotificationPriority.HIGH,
        expires_in_hours=168  # 1 week
    )

    stop_1 = driver_1.schedule_stop(
        street=streets[1],
        date='2025-09-14'
    )
    create_street_notification(
        title="Stop Scheduled",
        message=f"A stop was successfully scheduled by '{driver_1.get_fullname()}' at street '{streets[1].name}' for '2025-09-14'.",
        street=streets[1],
        notification_type=NotificationType.CONFIRMED,
        category=NotificationCategory.SCHEDULE,
        priority=NotificationPriority.HIGH,
        expires_in_hours=168  # 1 week
    )

    driver_1.mark_arrival(stop_1.id)
    create_street_notification(
        title="Driver Arrived!",
        message=f"'{driver_1.get_fullname()}' has arrived at your street.",
        street=streets[0],
        notification_type=NotificationType.ARRIVED,
        category=NotificationCategory.SERVICE,
        priority=NotificationPriority.URGENT,
        expires_in_hours=2  # Expires in 2 hours
    )

