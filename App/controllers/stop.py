import click

from App.models import Driver, Street, Stop, NotificationType
from App.models.enums import NotificationCategory, NotificationPriority
from App.extensions import db
from .notification import create_street_notification
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

'''
CREATE
'''
def create_stop(driver: Driver, street: Street, scheduled_date: str) -> Stop | None:
    """
    Create a stop for a street
    """
    try:
        new_stop = driver.schedule_stop(
            street=street,
            date=scheduled_date
        )

        if not new_stop:
            raise IntegrityError("Failed to create new stop.")

        # Notify residents with enhanced notification
        new_notification = create_street_notification(
            title="New Stop Scheduled",
            message=f"{driver.get_fullname()} has scheduled a stop for {street.name} on {scheduled_date}",
            street=street,
            notification_type=NotificationType.NEW,
            category=NotificationCategory.SCHEDULE,
            priority=NotificationPriority.HIGH,
            expires_in_hours=168  # Expires in 1 week
        )

        if not new_notification:
            raise IntegrityError("Failed to create notification for stop.")

        return new_stop
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Failed to create stop on {street.name}. {e}")
        return None


'''
GET
'''
def get_stop_by_id(id: str) -> Stop | None:
    """
    Get a stop by its id
    """
    return db.session.query(Stop).filter_by(id=id).one_or_none()

def stop_exists(street_name: str, scheduled_date: str) -> bool:
    """
    Check if a stop exists already
    """
    return db.session.query(Stop).filter_by(street_name=street_name, scheduled_date=scheduled_date, has_arrived=False).first() is not None

def get_all_stops() -> list[Stop]:

    return db.session.execute(db.select(Stop)).scalars().all()
'''
UPDATE
'''
def complete_stop(id: str) -> None:
    """
    Update a stop to be complete
    """
    stop = get_stop_by_id(id)

    if not stop:
        click.secho(f"[ERROR]: Failed to find stop with id '{id}'.", fg="red")
        return

    stop.complete()

    db.session.add(stop)
    db.session.commit()

'''
DELETE
'''
def delete_stop(id: str) -> None:
    """
    Delete a stop by its id
    """
    stop = get_stop_by_id(id)

    if not stop:
        click.secho(f"[ERROR]: Failed to find stop with id '{id}'.", fg="red")
        return

    db.session.delete(stop)
    db.session.commit()
