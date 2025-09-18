# Bread Van CLI — Command Reference (Updated)

A quick guide to all CLI commands in this project, matching the current code.

---

## ⚙️ Setup

```bash
pip install -r requirements.txt
flask init
```

## 🧭 Command Index

### Driver Commands
- `flask driver list [--filter string|json]`
- `flask driver schedule <driver_id> <street> <scheduled_date>`
- `flask driver inbox <driver_id> [--filter all|requested|confirmed]`
- `flask driver complete <driver_id> <stop_id>`
- `flask driver stops <driver_id>`
- `flask driver update <driver_id> [--status inactive|en_route|delivering] [--where "<text>"]`
- `flask driver status <driver_id>`

### Resident Commands
- `flask resident inbox <resident_id> [--filter all|requested|confirmed|arrived]`
- `flask resident request <resident_id>`

### Street Commands
- `flask street list [--filter string|json]`

### Auth Commands
- `flask auth list [--filter driver|resident]`
- `flask auth register --username <u> --password <p> --firstname <f> --lastname <l> [--role resident|driver] [--street "<name>"]`

---

## 🔢 Examples

### Drivers
```bash
flask driver list
flask driver schedule 3 "Murray Drive" "2025-01-23 07:30"
flask driver inbox 3 --filter requested
flask driver complete 3 12
flask driver stops 3
flask driver update 3 --status en_route --where "Near Oak Ave"
flask driver status 3
```

### Residents
```bash
flask resident inbox 7 --filter all
flask resident request 7
```

### Streets
```bash
flask street list
flask street list --filter json
```

### Auth
```bash
flask auth register --username bob --password pw --firstname Bob --lastname Brown --role driver
flask auth list --filter driver
```

---

## ✅ Notes & Behaviors

- **No session state**: all commands require explicit IDs.
- **Duplicate protection**: `driver schedule` prevents duplicate street+date.
- **Arrival side effect**: `driver complete` notifies residents and deletes stop requests for that street.
- **Output formatting**: errors = red, success = green.
