from .user import create_driver
from App.database import db
from .street import create_street
from .user import create_resident
from App.models import NotificationType
from .notification import create_notification


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
    create_notification(
        street=streets[0],
        notification_type=NotificationType.CONFIRMED,
        message=f"A stop was successfully scheduled by '{driver_1.get_fullname()}' at street '{streets[0].name}' for '2025-09-14'.",
    )

    driver_2.schedule_stop(
        street=streets[0],
        date='2025-09-20'
    )
    create_notification(
        street=streets[0],
        notification_type=NotificationType.CONFIRMED,
        message=f"A stop was successfully scheduled by '{driver_2.get_fullname()}' at street '{streets[0].name}' for '2025-09-20'.",
    )

    stop_1 = driver_1.schedule_stop(
        street=streets[1],
        date='2025-09-14'
    )
    create_notification(
        street=streets[1],
        notification_type=NotificationType.CONFIRMED,
        message=f"A stop was successfully scheduled by '{driver_1.get_fullname()}' at street '{streets[1].name}' for '2025-09-14'.",
    )

    driver_1.mark_arrival(stop_1.id)
    create_notification(
        notification_type=NotificationType.ARRIVED,
        message=f"'{driver_1.get_fullname()}' has arrived at your street.",
        street = streets[0]
    )

