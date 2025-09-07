from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db
from .enums import DriverStatus

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    username =  db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, username, password, first_name, last_name):
        self.username = username
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name

    def get_json(self):
        return{
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

    def set_password(self, password) -> None:
        """Create hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password) -> bool:
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def get_fullname(self) -> str:
        """Get user's fullname."""


class Driver (User):
    status = db.Column(db.String(), nullable=False, default=DriverStatus.INACTIVE)
    current_location = db.Column(db.String(255), nullable=False)

    def __init__(self, username, password, first_name, last_name):
        super().__init__(username, password, first_name, last_name)

    def get_json(self):
        return {
            **super().get_json(), # dict unpack
            'status': self.status,
            'current_location': self.current_location
        }

    def get_current_status(self) -> str:
        """Get the current status and location of the driver"""
        return f'{self.get_fullname()} is currently {self.status} at {self.current_location}'

    def 