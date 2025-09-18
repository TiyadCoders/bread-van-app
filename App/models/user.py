import click
from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db
from .enums import DriverStatus, NotificationType
from .street import Street
from .stop import Stop
from .notification import Notification
from abc import abstractmethod
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from .stop_request import StopRequest


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    username =  db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)

    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }

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
        return f"{self.first_name} {self.last_name}"

    @abstractmethod
    def view_inbox(self, filter: str | None = None) -> None:
        pass

    def __repr__(self):
        return f"<User {self.id} {self.get_fullname()}>"

class Driver(User):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    status = db.Column(db.String(), nullable=False, default=DriverStatus.INACTIVE.value)
    current_location = db.Column(db.String(255))

    # Relationships
    stops = db.relationship('Stop', back_populates='driver', cascade='all, delete-orphan', lazy='selectin')

    __mapper_args__ = {
        'polymorphic_identity': 'driver'
    }

    def __init__(self, username, password, first_name, last_name):
        super().__init__(username, password, first_name, last_name)
        self.status = DriverStatus.INACTIVE.value

    def get_json(self) -> dict[str, any]:
        return {
            **super().get_json(), # dict unpack
            'status': self.status,
            'current_location': self.current_location
        }

    def get_current_status(self) -> str:
        """Get the current status and location of the driver"""
        return f'{self.get_fullname()} is currently {self.status} at {self.current_location}'

    def schedule_stop(self, street: Street, date: str) -> Stop | None:
        """Schedule a stop for a given street"""
        try:
            # Create a stop
            new_stop = Stop(self, street, date)

            db.session.add(new_stop)
            db.session.commit()

            return new_stop
        except SQLAlchemyError as e:
            click.secho(f"[ERROR] {e}.", fg="red")
            db.session.rollback()
            return None
        pass

    @staticmethod
    def mark_arrival(stop_id: str) -> bool:
        """Notify residents of arrival"""
        stop: Stop | None = db.session.query(Stop).filter_by(id=stop_id).one_or_none()

        if not stop:
            click.secho(f"[ERROR]: Failed to find stop with id '{stop_id}'.", fg="red")
            return False

        if stop.has_arrived:
            click.secho(f"[ERROR]: Stop id '{stop_id}' has already been completed.", fg="red")
            return False

        stop.complete()

        click.secho(f"Successfully completed stop id '{stop_id}'.", fg="green")

        db.session.add(stop)
        db.session.commit()
        return True

    def update_status(self, driver_status: str | None, where: str) -> None:
        """Update the driver status"""
        if not driver_status and not where:
            return

        if driver_status:
            self.status = driver_status
        if where:
            self.current_location = where

        db.session.add(self)
        db.session.commit()

    def view_inbox(self, filter: str | None = None) -> None:
        """View stop request notifications"""
        notifications: list[Notification] = []

        if filter == "all":
            notifications = (
                db.session.query(Notification)
                .filter(Notification.type.in_([NotificationType.REQUESTED.value, NotificationType.CONFIRMED.value]))
                .order_by(Notification.created_at.asc()) # newest last
                .all()
            )
        elif filter in [NotificationType.REQUESTED.value, NotificationType.CONFIRMED.value]:
            notifications = (
                db.session.query(Notification)
                .filter_by(type=filter)
                .order_by(Notification.created_at.asc()) # newest last
                .all()
            )

        if not notifications:
            click.secho("Inbox is empty.", fg="yellow")
            return

        for notif in notifications:
            print(notif.to_string())

    def __repr__(self):
        return f"<Driver {self.id} {self.get_fullname()}>"

class Resident(User):
    __tablename__ = 'residents'
    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    street_name = db.Column(db.String(255))

    # Relationships
    stop_requests = db.relationship('StopRequest', back_populates='resident', cascade='all, delete-orphan', lazy='selectin')

    __mapper_args__ = {
        'polymorphic_identity': 'resident'
    }

    def __init__(self, username: str, password: str, first_name: str, last_name: str, street_name: str):
        super().__init__(username, password, first_name, last_name)
        self.street_name = street_name

    def get_json(self) -> dict[str, any]:
        return {
            **super().get_json(), # dict unpack
            'street_name': self.street_name
        }

    def request_stop(self) -> bool:
        """Request a stop for this resident's street"""
        new_request = StopRequest(self)

        # Check if it has stop requests already for street
        has_stop_request = StopRequest.query.filter_by(street_name=self.street_name).first() is not None

        if has_stop_request:
            click.secho(f"[WARNING]: Stop requests already exists for street '{self.street_name}'", fg="yellow")
            return False

        db.session.add(new_request)
        db.session.commit()

        return True

    def view_inbox(self, filter: str | None = None) -> None:
        """View stop notifications"""
        notifications: list[Notification] = []

        if filter == "all":
            notifications = (
                db.session.query(Notification)
                .filter(
                    or_(
                        Notification.street_name == self.street_name,
                        Notification.street_name.is_(None),
                    )
                )
                .order_by(Notification.created_at.asc())  # newest last
                .all()
            )
        elif filter in [
            NotificationType.REQUESTED.value,
            NotificationType.CONFIRMED.value,
            NotificationType.ARRIVED.value,
        ]:
            notifications = (
                db.session.query(Notification)
                .filter(
                    and_(
                        or_(
                            Notification.street_name == self.street_name,
                            Notification.street_name.is_(None),
                        ),
                        Notification.type == filter,
                    )
                )
                .order_by(Notification.created_at.asc())  # newest last
                .all()
            )

        if not notifications:
            click.secho("Inbox is empty.", fg="yellow")
            return

        for notif in notifications:
            print(notif.to_string())