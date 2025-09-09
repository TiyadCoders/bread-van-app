Bread Van CLI — Command Reference
====================================

A user-friendly guide to all CLI commands for the Bread Van assignment.

---

⚙️ Setup (once per machine)
---------------------------

```bash
# 1) Activate your virtualenv and install deps
pip install -r requirements.txt

# 2) Initialize database + seed data
flask init
```

> If `flask` says a command doesn’t exist, imports likely failed. Re-check `FLASK_APP` and fix any stack traces first.

---

🔐 Authentication & Session
---------------------------

These commands manage the current CLI session user.

```bash
# Create an account (role is 'resident' by default)
flask auth register --username alice --password secret \
  --firstname Alice --lastname Adams --role resident --street "Murray Drive"

# Log in
flask auth login --username alice --password secret

# Who am I?
flask auth profile

# Log out
flask auth logout
```

**Roles supported:** `resident`, `driver`  
Some commands require a specific role (see below).

---

🧭 Command Index (by role)
--------------------------

### Admin / Setup
- `flask init` — Create & initialize the database (and seed data).

### Driver Commands (login required as **driver**)
- `flask driver list [--f string|json]` — List all drivers.
- `flask driver schedule <street> <scheduled_date>` — **Schedule a stop** for a street.
- `flask driver inbox [--filter all|requested|confirmed]` — View driver inbox.
- `flask driver complete <stop_id>` — Mark arrival for a stop (notifies residents).
- `flask driver stops` — View your stops (created/arrived).
- `flask driver update [--status inactive|en_route|delivering] [--where "<text>"]` — Update current status/location.
- `flask driver status <driver_id>` — View a driver’s status & location (available to both roles).

### Resident Commands (login required as **resident**)
- `flask resident inbox [--filter all|requested|confirmed|arrived]` — View your inbox.
- `flask resident request` — Request a stop for your street.

### Streets (no login required in this CLI)
- `flask street list [--f string|json]` — List streets.

---

🧪 Quick Start Workflows
------------------------

### A) Resident workflow
```bash
# Register + login as resident
flask auth register --username eve --password secret \
  --firstname Eve --lastname Evans --role resident --street "Murray Drive"
flask auth login --username eve --password secret

# Check inbox (initially empty or seeded notices)
flask resident inbox --filter all

# Request a stop for your street
flask resident request

# Later, see updates (confirmed/arrived)
flask resident inbox --filter confirmed
flask resident inbox --filter arrived
```

### B) Driver workflow
```bash
# Register + login as driver
flask auth register --username bob --password secret \
  --firstname Bob --lastname Brown --role driver
flask auth login --username bob --password secret

# Update status/location (optional)
flask driver update --status en_route --where "Near Oak Ave"

# Schedule a stop for a street (date is free-form; use consistent format)
flask driver schedule "Murray Drive" "2025-01-23 07:30"

# See your stops
flask driver stops

# View your inbox (e.g., resident requests)
flask driver inbox --filter requested

# Mark arrival for a stop ID (copy an ID from `driver stops`)
flask driver complete 12
```

### C) Anyone: view a driver’s status
```bash
# As resident or driver (after login): show current status/location
flask driver status 3
```

---

🧩 Command Details
------------------

### `flask init`
Initialize + seed the database. Run once to set up local data.

---

### `flask auth register`
Create a new user.

**Options**
- `--username <str>` (required)
- `--password <str>` (required)
- `--firstname <str>` (required)
- `--lastname <str>` (required)
- `--role <resident|driver>` (default: `resident`)
- `--street <str>` (required for residents to attach their street)

**Examples**
```bash
flask auth register --username jane --password pw \
  --firstname Jane --lastname Jones --role driver

flask auth register --username rick --password pw \
  --firstname Rick --lastname Ross --role resident --street "Murray Drive"
```

---

### `flask auth login`
Login and persist session.

**Options**
- `--username <str>` (required)
- `--password <str>` (required)

---

### `flask auth profile`
Show the current session user.

---

### `flask auth logout`
Clear the current session.

---

### `flask driver list`
List drivers.

**Options**
- `--f string|json` (default: `string`)

**Examples**
```bash
flask driver list
flask driver list --f json
```

---

### `flask driver schedule <street> <scheduled_date>`
Schedule a stop for a given street.

- **Role:** driver
- **Args:**
  - `street` — street name (must exist)
  - `scheduled_date` — free-form string (e.g., `2025-01-23 07:30`)

**Example**
```bash
flask driver schedule "Murray Drive" "2025-01-23 07:30"
```

---

### `flask driver inbox [--filter ...]`
View driver inbox.

**Options**
- `--filter all|requested|confirmed` (default: `all`)

**Examples**
```bash
flask driver inbox
flask driver inbox --filter requested
flask driver inbox --filter confirmed
```

---

### `flask driver complete <stop_id>`
Mark arrival at a stop and notify residents.

**Args**
- `stop_id` — from `flask driver stops`

**Example**
```bash
flask driver complete 12
```

---

### `flask driver stops`
View all stops for the logged-in driver.

**Example**
```bash
flask driver stops
```

---

### `flask driver update [--status ...] [--where ...]`
Update driver status (and optional location string).

**Options**
- `--status inactive|en_route|delivering`
- `--where "<free text>"`

**Examples**
```bash
flask driver update --status delivering
flask driver update --status en_route --where "Murray & 3rd"
```

---

### `flask driver status <driver_id>`
View a driver’s current status + location.

- **Role:** driver or resident
- **Args:** `driver_id` (numeric)

**Example**
```bash
flask driver status 3
```

---

### `flask resident inbox [--filter ...]`
View your inbox of notifications.

**Options**
- `--filter all|requested|confirmed|arrived` (default: `all`)

**Examples**
```bash
flask resident inbox
flask resident inbox --filter requested
flask resident inbox --filter confirmed
flask resident inbox --filter arrived
```

---

### `flask resident request`
Request a stop for **your** street (as recorded on your profile).

**Example**
```bash
flask resident request
```

---

### `flask street list [--f ...]`
List streets.

**Options**
- `--f string|json` (default: `string`)

**Examples**
```bash
flask street list
flask street list --f json
```

---

✅ Tips
------

- **Date/Time:** `scheduled_date` is a free-form string; prefer consistent formats (e.g., `YYYY-MM-DD HH:MM`).  
- **Filters:** Valid values are enforced; typos will show a helpful error.  
- **Roles:** Commands check your role via session; use `auth login` with the right account.  
- **IDs:** Use `flask driver stops` to find a `stop_id` for `driver complete`.  
- **Streets:** Make sure streets exist (seeded during `flask init`) before scheduling or requesting.

---

🧰 Troubleshooting
------------------

- **Permission denied:** log in as the correct role (`resident` vs `driver`).  
- **Street not found:** check spelling or seed streets during `flask init`.
