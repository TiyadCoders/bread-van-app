import warnings
# Remove warning
warnings.filterwarnings(
    "ignore",
    message=r".*pkg_resources is deprecated as an API.*",
    category=UserWarning,
)
import click
from flask.cli import AppGroup
from App.utils import (
    requires_login,
    whoami,
    login_cli,
    clear_session
)
from App.database import get_migrate
from App.main import create_app
from App.models import (
    Street,
    Driver,
    NotificationType,
    Resident,
    DriverStatus
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
    get_driver_by_id
)


'''
Initial Setup
'''
app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
# flask init
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database initialized')


'''
Driver Commands
'''
# e.g. flask driver <command>
driver_cli = AppGroup('driver', help="Driver commands")

@driver_cli.command("list", help="List drivers in the database")
@click.option("--f", default="string")
@requires_login(['driver', 'resident'])
def list_driver_command(f):
    """View all available drivers"""
    if f == 'string':
        print(get_all_drivers())
    elif f == 'json':
        print(get_all_drivers_json())
    else:
        click.secho("[ERROR]: Invalid form argument. (json, string)", fg="red")


@driver_cli.command("schedule", help="Schedule a stop for a street")
@click.argument("street")
@click.argument("scheduled_date")
@requires_login(['driver'])
def driver_schedule_stop(street: str, scheduled_date: str):
    """[Driver] Use case 1: Schedule a stop for a street"""
    driver: Driver = whoami()
    street_obj: Street | None = get_street_by_string(street)

    if street_obj is None:
        click.secho(f"[ERROR]: Street '{street}' not found.", fg="red")
        return

    new_stop = driver.schedule_stop(street_obj, scheduled_date)

    if new_stop:
        create_notification(
            street=street_obj,
            notification_type=NotificationType.CONFIRMED,
            message=f"A stop was successfully scheduled by '{driver.get_fullname()}' at street '{street_obj.name}' for '{scheduled_date}'."
        )
        click.secho(f"Successfully scheduled a stop to '{street_obj.name}'.", fg="green")
    else:
        click.secho(f"[ERROR]: Failed to schedule a stop to '{street_obj.name}'.", fg="red")


@driver_cli.command("inbox", help="View driver inbox")
@click.option("--filter", default="all")
@requires_login(['driver'])
def driver_view_inbox(filter: str):
    """[Driver] Use case 2: View requested stops"""
    if filter not in ['all', NotificationType.REQUESTED.value, NotificationType.CONFIRMED.value]:
        click.secho("[ERROR]: '--filter' accepts ('all', 'requested', 'confirmed')", fg="red")
        return

    driver: Driver = whoami()
    driver.view_inbox(filter)

@driver_cli.command("complete", help="Notify residents of arrival at stop. Use 'flask driver stops' to view notifications and copy the id from a message")
@click.argument("stop_id")
@requires_login(['driver'])
def driver_mark_arrival(stop_id: str):
    """[Driver] Use case 3: Mark arrival for a stop on a street"""
    driver: Driver = whoami()

    if driver.mark_arrival(stop_id):
        create_notification(
            notification_type=NotificationType.ARRIVED,
            message=f"'{driver.get_fullname()}' has arrived at your street."
        )


@driver_cli.command("stops", help="View stops for driver")
@requires_login(['driver'])
def driver_view_stops():
    """[Driver] Use case 4: View stops"""
    driver: Driver = whoami()
    for stop in driver.stops:
        colour = "yellow" if not stop.has_arrived else "green"
        (click.secho(f"[Created {stop.created_at}]\t{stop.id}) {stop.to_string()}", fg=colour))


@driver_cli.command("update", help="Update driver status")
@click.option("--status")
@click.option("--where")
@requires_login(['driver'])
def driver_update_status(status: str | None, where: str | None):
    """[Driver] Use case 5: Update status"""
    driver: Driver = whoami()

    if status and status not in ['all', *[_.value for _ in (DriverStatus.INACTIVE, DriverStatus.EN_ROUTE, DriverStatus.DELIVERING)]]:
        click.secho("[ERROR]: '--filter' accepts ('inactive', 'en_route', 'delivering')", fg="red")
        return

    driver.update_status(driver_status=status, where=where)
    click.secho("Successfully updated your status.", fg="green")


@driver_cli.command("status", help="View driver status")
@click.argument("driver_id")
@requires_login(['driver', 'resident'])
def driver_view_status(driver_id: str):
    """[Resident] Use case 3: View driver status and location"""
    driver = get_driver_by_id(driver_id)

    if not driver:
        click.secho(f"[ERROR]: Could not find driver with id {driver_id}.", fg="red")
        return

    print(driver.get_current_status())

app.cli.add_command(driver_cli) # add group to the cli

'''
Resident Commands
'''
# e.g. flask resident <command>
resident_cli = AppGroup('resident', help="Resident commands")

@resident_cli.command("inbox", help="View stops for driver")
@click.option("--filter", default="all")
@requires_login(['resident'])
def resident_view_inbox(filter: str):
    """[Resident] Use case 1: View inbox for scheduled drivers for street"""
    if filter not in ['all', *[ _.value for _ in (NotificationType.REQUESTED, NotificationType.CONFIRMED, NotificationType.ARRIVED)]]:
        click.secho("[ERROR]: '--filter' accepts ('all', 'requested', 'confirmed', 'arrived')", fg="red")
        return

    resident: Resident = whoami()
    resident.view_inbox(filter)


@resident_cli.command("request", help="Request a stop for street")
@requires_login(['resident'])
def resident_request_stop():
    """[Resident] Use case 2: Request a  stop for street"""
    resident: Resident = whoami()
    resident.request_stop()

    create_notification(
        message=f"'{resident.get_fullname()}' has requested a stop for street '{resident.street_name}'.",
        notification_type=NotificationType.REQUESTED,
        street=get_street_by_string(resident.street_name)
    )

    click.secho(f"Request was made.", fg="green")


app.cli.add_command(resident_cli) # add group to the cli

'''
Street Commands
'''
# e.g. flask street <command>
street_cli = AppGroup('street', help="Street commands")

@street_cli.command("list", help="List streets in the database")
@click.option("--f", default="string")
def list_street_command(f: str):
    """View streets available"""
    if f == 'string':
        print(get_all_streets())
    elif f == 'json':
        print(get_all_streets_json())
    else:
        click.secho("[ERROR]: Invalid form argument. hint=('json', 'string')", fg="red")

app.cli.add_command(street_cli) # add group to the cli


'''
Auth Commands
'''
# e.g. flask auth <command>
auth_cli = AppGroup("auth", help="Authentication commands")

@auth_cli.command("login", help="Log in and persist session")
@click.option("--username", required=True)
@click.option("--password", required=True)
def auth_login(username, password):
    """[Guest] Use case 1: Login"""
    if login_cli(username, password):
        u = whoami()
        click.secho(f"Logged in as {u.username} ({u.first_name} {u.last_name})", fg="green")
    else:
        click.secho("[ERROR]: Invalid credentials.", fg="red")


@auth_cli.command("register", help="Create an account")
@click.option("--username", required=True)
@click.option("--password", required=True)
@click.option("--firstname", required=True)
@click.option("--lastname", required=True)
@click.option("--role", default="resident")
@click.option("--street")
def auth_register(username: str, password: str, firstname: str, lastname: str, role: str, street: str):
    """[Guest] Use case 2: Register"""
    register_user(username, password, firstname, lastname, role, street)


@auth_cli.command("logout", help="Clear session")
def auth_logout():
    """Logout of current session"""
    clear_session()
    click.secho("Logged out.", fg="yellow")


@auth_cli.command("profile", help="Show current session user")
def auth_whoami():
    """View currently logged-in user"""
    u = whoami()
    if not u:
        click.secho("[ERROR]: Not logged in.", fg="red")
        return
    click.echo(f"{u.username} ({u.first_name} {u.last_name})")

app.cli.add_command(auth_cli)