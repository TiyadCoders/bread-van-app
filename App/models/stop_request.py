from App.database import db
from datetime import  datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import Resident

class StopRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    street_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.String(27), nullable=False)

    # Relationships
    resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'), nullable=False)
    resident = db.relationship('Resident', back_populates='stop_requests', lazy='joined')

    def __init__(self, resident: 'Resident'):
        self.resident_id = resident.id
        self.street_name = resident.street_name
        self.created_at = datetime.utcnow().isoformat()

    def get_json(self) -> dict[str, str]:
        return {
            'id': self.id,
            'resident_id': self.resident_id,
            'street_name': self.street_name,
            'created_at': self.created_at
        }
