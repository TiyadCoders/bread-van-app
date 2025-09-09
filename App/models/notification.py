from App.database import db
from .street import Street
from .enums import NotificationType
import datetime as dt

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    street_name = db.Column(db.String(255))
    created_at = db.Column(db.String(27), nullable=False)

    def __init__(self, message: str, street: Street | None, notification_type: NotificationType):
        self.message = message
        self.type = notification_type.value
        self.created_at = dt.datetime.utcnow().isoformat()

        if street:
            self.street_name = street.name

    def get_json(self) -> dict[str, str]:
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'street_name': self.street_name,
            'created_at': self.created_at
        }

    def to_string(self):
        return f"[Created {self.created_at}]\t{self.message}"