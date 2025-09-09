import click

from App.models import Driver, Street, Stop, NotificationType
from App.database import db
from .notification import create_notification
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

        # Notify residents
        new_notification = create_notification(
            street=street,
            notification_type=NotificationType.NEW,
            message=f"[{new_stop.created_at}]\t{driver.get_fullname()} has scheduled a stop for {street.name} on {scheduled_date}"
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