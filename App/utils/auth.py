import json
import click

from functools import wraps
from flask.cli import with_appcontext

from App import get_user, get_user_by_type
from App.config import SESSION_FILE
from App.database import db
from App.models import User
from sqlalchemy.exc import SQLAlchemyError

def save_session(user_id: str):
    with open(SESSION_FILE, "w") as f:
        json.dump({"user_id": user_id}, f)

def load_session() -> str | None:
    if SESSION_FILE.exists():
        with open(SESSION_FILE) as f:
            return json.load(f).get("user_id")
    return None

def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()

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
            user = whoami()
            if not user:
                raise click.ClickException("Not logged in. Use 'flask auth login'")

            if not (user.type in roles):
                raise click.ClickException("User is not authorized.")
            return fn(*args, **kwargs)
        return wrapper
    return f