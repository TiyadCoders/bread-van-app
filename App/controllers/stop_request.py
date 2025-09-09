from App.models import StopRequest
from App.database import db
from typing import TYPE_CHECKING
from .notification import create_notification
from .. import NotificationType, get_street_by_string

if TYPE_CHECKING:
    from App.models import Resident

'''
CREATE
'''
def create_stop_request(resident: Resident):
    """
    Create a stop request for a resident's street
    """
    db.session.add(StopRequest(resident))
    db.session.commit()

    create_notification(
        message=f"'{resident.get_fullname()}' has requested a stop for street '{resident.street_name}'.",
        notification_type=NotificationType.REQUESTED,
        street=get_street_by_string(resident.street_name)
    )

