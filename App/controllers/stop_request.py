from App.models import StopRequest, Street
from App.database import db
from typing import TYPE_CHECKING
from .notification import create_notification
from .. import NotificationType

if TYPE_CHECKING:
    from App.models import Resident

'''
CREATE
'''
def stop_request_exists(street_name: str) -> bool:
    """
    Check if a stop request exists already
    """
    return db.session.query(StopRequest).filter_by(street_name=street_name).first() is not None


'''
DELETE
'''
def delete_stop_requests(street_name: str) -> None:
    """
    Delete all stop requests for a street
    """
    db.session.query(StopRequest).filter_by(street_name=street_name).delete()
    db.session.commit()