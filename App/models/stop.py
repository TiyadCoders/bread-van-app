from App.extensions import db
from .street import Street
from typing import TYPE_CHECKING
import datetime as dt

if TYPE_CHECKING:
    from .user import Driver


class Stop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    street_name = db.Column(db.String(255), nullable=False)
    scheduled_date = db.Column(db.String(27), nullable=False)
    created_at = db.Column(db.String(27), nullable=False)
    has_arrived = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    driver = db.relationship('Driver', back_populates='stops', lazy='joined')

    def __init__(self, driver: 'Driver', street: Street, scheduled_date: str):
        self.driver_id = driver.id
        self.street_name = street.name
        self.scheduled_date = scheduled_date

        # Defaults
        self.has_arrived = False
        self.created_at = dt.datetime.utcnow().isoformat()

    def get_json(self) -> dict[str, any]:
        return {
            'id': self.id,
            'driverId': self.driver_id,
            'streetName': self.street_name,
            'scheduledDate': self.scheduled_date,
            'createdAt': self.created_at,
            'hasArrived': self.has_arrived
        }

    def to_api_dict(self) -> dict[str, any]:
        """Enhanced API serialization for stops"""
        return {
            'id': self.id,
            'driverId': self.driver_id,
            'driver': {
                'id': self.driver.id,
                'name': self.driver.get_fullname()
            } if self.driver else None,
            'streetName': self.street_name,
            'scheduledDate': self.scheduled_date,
            'createdAt': self.created_at,
            'hasArrived': self.has_arrived,
            'status': 'completed' if self.has_arrived else 'scheduled'
        }

    def complete(self) -> bool:
        """Mark the stop as completed - enhanced for API use"""
        if self.has_arrived:
            return False  # Already completed

        self.has_arrived = True
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def mark_arrival(self) -> bool:
        """API-friendly method to mark arrival"""
        return self.complete()

    def to_string(self):
        return f"A stop is scheduled for the street '{self.street_name}' at '{self.scheduled_date}'" if not self.has_arrived else f"A stop was made at '{self.scheduled_date}' on street '{self.street_name}'"
