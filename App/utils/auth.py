import json
import click

from functools import wraps
from flask.cli import with_appcontext

from App.controllers.user import get_user, get_user_by_type

from App.extensions import db
from App.models import User
from sqlalchemy.exc import SQLAlchemyError


def login_cli(username: str, password: str) -> bool:
    user = db.session.execute(
        db.select(User).where(User.username == username)
    ).scalar_one_or_none()
    if not user or not user.check_password(password):
        return False
    save_session(user.id)
    return True

def whoami(uid: str, type: str) -> User | None:
    if uid is None:
        return None

    user = get_user_by_type(uid, type)

    if not user:
        raise SQLAlchemyError(f'Failed to find user with id {uid}')

    return user

def requires_login(roles: list[str] | None = None):
    def f (fn):
        """Decorator for commands that require a logged-in user."""
        @wraps(fn)
        @with_appcontext
        def wrapper(*args, **kwargs):
            user_id = load_session()
            if not user_id:
                raise click.ClickException("Not logged in. Use 'flask auth login'")

            # For CLI, we need to determine user type by querying the user
            user = get_user(user_id)
            if not user:
                raise click.ClickException("Not logged in. Use 'flask auth login'")

            if roles and not (user.type in roles):
                raise click.ClickException("User is not authorized.")
            return fn(*args, **kwargs)
        return wrapper
    return f
