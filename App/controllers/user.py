import click
from App.models import User, Driver, Street, Resident, DriverStatus
from App.database import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .street import get_street_by_string

'''
CREATE
'''
def create_user(username, password, first_name, last_name) -> User:
    new_user = User(username=username, password=password, first_name=first_name, last_name=last_name)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def create_driver(username, password, first_name, last_name) -> Driver | None:
    try:
        new_driver = Driver(
            username,
            password,
            first_name,
            last_name
        )
        db.session.add(new_driver)
        db.session.commit()
        return new_driver
    except IntegrityError:
        click.secho(f"[ERROR]: User already exists with that username.", fg="red")
        db.session.rollback()
        return None
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e

def create_resident(username: str, password: str, first_name: str, last_name: str, street: Street) -> Resident | None:
    try:
        new_resident = Resident(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            street_name=street.name
        )
        db.session.add(new_resident)
        db.session.commit()
        return new_resident
    except IntegrityError:
        click.secho(f"[ERROR]: User already exists with that username.", fg="red")
        db.session.rollback()
        return None
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e

def register_user(username: str, password: str, firstname: str, lastname: str, role: str, street: str) -> bool:
    if role == 'resident':
        if not street:
            click.secho("[ERROR]: '--street' option is required for resident registration", fg="red")
            return False

        street_obj = get_street_by_string(street)

        if not street_obj:
            click.secho("[ERROR]: --street does not exist. Use 'flask street list' to see available streets.", fg="red")
            return False

        if not create_resident(username=username, password=password, first_name=firstname, last_name=lastname, street=street_obj):
            return False

        click.secho("Successfully required user.", fg="green")
    elif role == 'driver':
        if not create_driver(username=username, password=password, first_name=firstname, last_name=lastname):
            return False
    else:
        click.secho(f"[ERROR]: role '{role}' does not exist.", fg="red")
        return False

    return True


'''
GET
'''
def get_user(id):
    return db.session.get(User, id)

def get_user_by_type(id, type: str) -> User | None:
    user = db.session.get(User, id)

    if user and user.type == type:
        return user

    return None


def get_all_users() -> list[User]:
    return db.session.scalars(db.select(User)).all()

def get_all_drivers() -> list[Driver]:
    return db.session.scalars(db.select(Driver)).all()

def get_all_drivers_json() -> list[dict[str, str]]:
    drivers = get_all_drivers()
    if not drivers:
        return []
    drivers = [driver.get_json() for driver in drivers]
    return drivers

def get_all_users_json() -> list[dict[str, str]]:
    users = get_all_users()
    if not users:
        return []
    users = [user.get_json() for user in users]
    return users

def get_driver_by_id(driver_id: str) -> Driver | None:
    return db.session.query(Driver).filter_by(id=driver_id).one_or_none()
