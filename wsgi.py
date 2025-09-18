import warnings

# Suppress a noisy setuptools warning in click help output
warnings.filterwarnings(
    "ignore",
    message=r".*pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

from typing import Optional, Iterable

import click
from flask.cli import AppGroup

from App.utils import whoami
from App.database import get_migrate
from App.main import create_app
from App.models import (
    Street,
    Driver,
    NotificationType,
    Resident,
    DriverStatus,
    User,
    Stop
)
from App.controllers import (
    initialize,
    get_all_streets_json,
    get_all_streets,
    get_all_drivers_json,
    get_all_drivers,
    get_street_by_string,
    register_user,
    create_notification,
    get_driver_by_id,
    stop_exists,
    delete_stop_requests
)

# --------------------------------------------------------------------------------------
# App Initialization
# --------------------------------------------------------------------------------------

app = create_app()
migrate = get_migrate(app)

# --------------------------------------------------------------------------------------
# Helpers & Constants
# --------------------------------------------------------------------------------------

VALID_DRIVER_INBOX_FILTERS = {"all", NotificationType.REQUESTED.value, NotificationType.CONFIRMED.value}
VALID_RESIDENT_INBOX_FILTERS = {"all", NotificationType.REQUESTED.value, NotificationType.CONFIRMED.value, NotificationType.ARRIVED.value}
VALID_USER_TYPES = {"driver", "resident"}
VALID_DRIVER_STATUSES = {DriverStatus.INACTIVE.value, DriverStatus.EN_ROUTE.value, DriverStatus.DELIVERING.value}


def resolve_user(user_id: str, role: str):
    """
    Try to resolve a user via whoami(user_id, role).
    On failure, prints a red error and returns None.
    """
    try:
        return whoami(user_id, role)
    except Exception as e:  # broad by request: catch anything from whoami path
        click.secho(f"[ERROR]: Failed to identify {role}. {e}", fg="red")
        return None


def echo_list(items: Iterable, color: Optional[str] = None) -> None:
    for item in items:
        if color:
            click.secho(str(item), fg=color)
        else:
            click.echo(str(item))


# --------------------------------------------------------------------------------------
# Top-level Commands
# --------------------------------------------------------------------------------------

# flask init
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    click.secho("Database initialized.", fg="green")


# --------------------------------------------------------------------------------------
# Driver Commands
# --------------------------------------------------------------------------------------

driver_cli = AppGroup("driver", help="Driver commands")

@driver_cli.command("list", help="List drivers in the database")
@click.option("--filter", "fmt", default="string", help="Format: 'string' or 'json'")
def list_driver_command(fmt: str):
    """View all available drivers."""
    if fmt == "string":
        echo_list(get_all_drivers())
    elif fmt == "json":
        click.echo(get_all_drivers_json())
    else:
        click.secho("[ERROR]: Invalid format. Use 'json' or 'string'.", fg="red")


@driver_cli.command("schedule", help="Schedule a stop for a street")
@click.argument("driver_id")
@click.argument("street")
@click.argument("scheduled_date")
def driver_schedule_stop(driver_id: str, street: str, scheduled_date: str):
    """[Driver] Use case 1: Schedule a stop for a street."""
    driver: Optional[Driver] = resolve_user(driver_id, "driver")
    if not driver:
        return

    street_obj: Optional[Street] = get_street_by_string(street)
    if street_obj is None:
        click.secho(f"[ERROR]: Street '{street}' not found.", fg="red")
        return

    # Prevent duplicate stop on same date/street
    if stop_exists(street_name=street_obj.name, scheduled_date=scheduled_date):
        click.secho(f"[ERROR]: Failed to schedule stop to '{street_obj.name}'. Already exists.", fg="red")
        return

    new_stop = driver.schedule_stop(street_obj, scheduled_date)
    if new_stop:
        create_notification(
            street=street_obj,
            notification_type=NotificationType.CONFIRMED,
            message=(
                f"A stop was successfully scheduled by '{driver.get_fullname()}' "
                f"at street '{street_obj.name}' for '{scheduled_date}'."
            ),
        )
        click.secho(f"Successfully scheduled a stop to '{street_obj.name}'.", fg="green")
    else:
        click.secho(f"[ERROR]: Failed to schedule a stop to '{street_obj.name}'.", fg="red")


@driver_cli.command("inbox", help="View driver inbox")
@click.argument("driver_id")
@click.option("--filter", "inbox_filter", default="all", help="Filter: 'all', 'requested', 'confirmed'")
def driver_view_inbox(driver_id: str, inbox_filter: str):
    """[Driver] Use case 2: View requested/confirmed stops."""
    driver: Optional[Driver] = resolve_user(driver_id, "driver")
    if not driver:
        return

    if inbox_filter not in VALID_DRIVER_INBOX_FILTERS:
        click.secho("[ERROR]: '--filter' accepts ('all', 'requested', 'confirmed')", fg="red")
        return

    driver.view_inbox(inbox_filter)


@driver_cli.command(
    "complete",
    help="Notify residents of arrival at stop. Use 'flask driver stops <driver_id>' to view stops and copy the stop id.",
)
@click.argument("driver_id")
@click.argument("stop_id")
def driver_mark_arrival(driver_id: str, stop_id: str):
    """[Driver] Use case 3: Mark arrival for a stop on a street."""
    driver: Optional[Driver] = resolve_user(driver_id, "driver")
    if not driver:
        return

    if driver.mark_arrival(stop_id):
        create_notification(
            notification_type=NotificationType.ARRIVED,
            message=f"'{driver.get_fullname()}' has arrived at your street.",
        )

        # Remove all stop requests for that street if successful
        stop: Optional[Stop] = Stop.query.get(stop_id)

        if not stop:
            click.secho("[ERROR]: Failed to fetch stop.", fg="red")
            return

        delete_stop_requests(stop.street_name)

        click.secho("Arrival recorded and residents notified.", fg="green")
    else:
        click.secho("[ERROR]: Failed to mark arrival for the provided stop id.", fg="red")


@driver_cli.command("stops", help="View stops for driver")
@click.argument("driver_id")
def driver_view_stops(driver_id: str):
    """[Driver] Use case 4: View stops."""
    driver: Optional[Driver] = resolve_user(driver_id, "driver")
    if not driver:
        return

    for stop in driver.stops:
        colour = "yellow" if not stop.has_arrived else "green"
        click.secho(f"[Created {stop.created_at}]\t{stop.id}) {stop.to_string()}", fg=colour)


@driver_cli.command("update", help="Update driver status")
@click.argument("driver_id")
@click.option("--status", help="One of: 'inactive', 'en_route', 'delivering'")
@click.option("--where", help="Optional free-text location string")
def driver_update_status(driver_id: str, status: Optional[str], where: Optional[str]):
    """[Driver] Use case 5: Update status (and optionally location)."""
    driver: Optional[Driver] = resolve_user(driver_id, "driver")
    if not driver:
        return

    if status and status not in VALID_DRIVER_STATUSES:
        click.secho("[ERROR]: '--status' accepts ('inactive', 'en_route', 'delivering')", fg="red")
        return

    driver.update_status(driver_status=status, where=where)
    click.secho("Successfully updated your status.", fg="green")


@driver_cli.command("status", help="View driver status")
@click.argument("driver_id")
def driver_view_status(driver_id: str):
    """[Resident] Use case 3: View driver status and location."""
    driver = get_driver_by_id(driver_id)
    if not driver:
        click.secho(f"[ERROR]: Could not find driver with id '{driver_id}'.", fg="red")
        return

    click.echo(driver.get_current_status())


app.cli.add_command(driver_cli)  # register driver group

# --------------------------------------------------------------------------------------
# Resident Commands
# --------------------------------------------------------------------------------------

resident_cli = AppGroup("resident", help="Resident commands")

@resident_cli.command("inbox", help="View resident inbox")
@click.argument("resident_id")
@click.option("--filter", "inbox_filter", default="all", help="Filter: 'all', 'requested', 'confirmed', 'arrived'")
def resident_view_inbox(resident_id: str, inbox_filter: str):
    """[Resident] Use case 1: View inbox for scheduled drivers for street."""
    resident: Optional[Resident] = resolve_user(resident_id, "resident")
    if not resident:
        return

    if inbox_filter not in VALID_RESIDENT_INBOX_FILTERS:
        click.secho("[ERROR]: '--filter' accepts ('all', 'requested', 'confirmed', 'arrived')", fg="red")
        return

    resident.view_inbox(inbox_filter)


@resident_cli.command("request", help="Request a stop for your street")
@click.argument("resident_id")
def resident_request_stop(resident_id: str):
    """[Resident] Use case 2: Request a stop for street."""
    resident: Optional[Resident] = resolve_user(resident_id, "resident")
    if not resident:
        return

    if resident.request_stop():
        create_notification(
            message=f"'{resident.get_fullname()}' has requested a stop for street '{resident.street_name}'.",
            notification_type=NotificationType.REQUESTED,
            street=get_street_by_string(resident.street_name),
        )
        click.secho("Request was made.", fg="green")


app.cli.add_command(resident_cli)  # register resident group

# --------------------------------------------------------------------------------------
# Street Commands
# --------------------------------------------------------------------------------------

street_cli = AppGroup("street", help="Street commands")

@street_cli.command("list", help="List streets in the database")
@click.option("--filter", "fmt", default="string", help="Format: 'string' or 'json'")
def list_street_command(fmt: str):
    """View streets available."""
    if fmt == "string":
        echo_list(get_all_streets())
    elif fmt == "json":
        click.echo(get_all_streets_json())
    else:
        click.secho("[ERROR]: Invalid format. Use 'json' or 'string'.", fg="red")


app.cli.add_command(street_cli)  # register street group

# --------------------------------------------------------------------------------------
# Auth Commands
# --------------------------------------------------------------------------------------

auth_cli = AppGroup("auth", help="Authentication commands")

@auth_cli.command("list", help="Show a list of users")
@click.option("--filter", "user_type", help="Optional: 'driver' or 'resident'")
def auth_list(user_type: Optional[str]):
    """Get a list of users."""
    users: Optional[list[User]] = None

    if user_type:
        if user_type not in VALID_USER_TYPES:
            click.secho("[ERROR]: Invalid '--filter'. Use 'driver' or 'resident'.", fg="red")
            return
        users = User.query.filter_by(type=user_type).all()
    else:
        users = User.query.all()

    if users:
        echo_list(users)
    else:
        click.secho("Users not found.", fg="yellow")


@auth_cli.command("register", help="Create an account")
@click.option("--username", required=True)
@click.option("--password", required=True)
@click.option("--firstname", required=True)
@click.option("--lastname", required=True)
@click.option("--role", default="resident", help="One of: 'resident', 'driver'")
@click.option("--street", help="Required for resident accounts")
def auth_register(username: str, password: str, firstname: str, lastname: str, role: str, street: Optional[str]):
    """[Guest] Use case 2: Register."""
    register_user(username, password, firstname, lastname, role, street)
    click.secho("Registration successful.", fg="green")


app.cli.add_command(auth_cli)  # register auth group