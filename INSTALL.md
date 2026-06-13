# VetAnesthesia Records — Installation Guide

This app runs as a local web server.  Any computer on the same Wi-Fi can open
it in a browser — no internet required.

---

## Contents

1. [What you need](#1-what-you-need)
2. [Option A — Docker install (recommended)](#option-a--docker-install-recommended)
3. [Option B — Manual install (no Docker)](#option-b--manual-install-no-docker)
4. [First login & admin setup](#first-login--admin-setup)
5. [How other devices connect](#how-other-devices-connect)
6. [Backup & restore](#backup--restore)
7. [Transferring to another computer](#transferring-to-another-computer)
8. [Stopping the server](#stopping-the-server)
9. [Changing the port](#changing-the-port)
10. [Troubleshooting](#troubleshooting)

---

## 1. What you need

| | Docker (Option A) | Manual (Option B) |
|---|---|---|
| Docker Desktop | ✅ Required | ✗ Not needed |
| Python 3.9+ | ✗ Not needed | ✅ Required |
| Disk space | ~500 MB | ~200 MB |
| Works on | Windows, Mac, Linux | Windows, Mac, Linux |

---

## Option A — Docker install (recommended)

Docker packages everything (Python, libraries, the app) into one container.
No need to install Python or any dependencies separately.

### Step 1 — Install Docker Desktop

Download from **https://www.docker.com/products/docker-desktop** and install it.
After installation, open Docker Desktop and wait for it to show "Engine running".

### Step 2 — Copy the app folder to the new computer

Copy the entire `vet-anesthesia` folder to the new computer.
You can use a USB drive, shared network folder, or zip file.

### Step 3 — Open a terminal in the app folder

**Windows:** Right-click inside the `vet-anesthesia` folder → "Open in Terminal"
**Mac:** Right-click the folder → "New Terminal at Folder" (or `cd` to it in Terminal)

### Step 4 — Start the app

```bash
docker compose up -d
```

First run will build the image (~3–5 minutes). Subsequent starts take 5 seconds.

### Step 5 — Open the app

Open a browser and go to: **http://localhost:8100**

The app is now running. See [How other devices connect](#how-other-devices-connect)
to share it with other computers on the network.

### Docker commands reference

```bash
docker compose up -d        # Start in background
docker compose down         # Stop
docker compose logs -f      # View live logs
docker compose restart      # Restart after config change
docker compose build --no-cache && docker compose up -d   # Rebuild after app update
```

---

## Option B — Manual install (no Docker)

### Step 1 — Install Python 3.9 or newer

**Mac:** Install from https://www.python.org/downloads/ or use Homebrew:
```bash
brew install python3
```

**Windows:** Download from https://www.python.org/downloads/
During install, check **"Add Python to PATH"**.

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip
```

Verify:
```bash
python3 --version    # should show 3.9 or higher
```

### Step 2 — Copy the app folder

Copy the entire `vet-anesthesia` folder to the new computer.

### Step 3 — Install dependencies

Open a terminal inside the `vet-anesthesia` folder and run:

```bash
pip3 install -r requirements.txt
```

On some systems you may need:
```bash
pip3 install -r requirements.txt --break-system-packages
```

### Step 4 — Start the app

**Mac / Linux:**
```bash
bash start.sh
```

**Windows:**
```cmd
python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

You will see:
```
======================================================
  VetAnesthesia Records
======================================================
  This computer:
    http://localhost:8100
  Other devices on the same Wi-Fi/network:
    http://192.168.x.x:8100
======================================================
```

### Step 5 — Open the app

Open a browser and go to: **http://localhost:8100**

---

## First login & admin setup

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin1234` |

**Change the password immediately** after first login:
1. Go to the Users panel (admin sidebar)
2. Create a new admin user with your own username/password
3. Delete the default `admin` account (or change its password)

### Creating user accounts

1. Log in as admin
2. Click the **☰ menu → Users** in the sidebar
3. Click **+ Add User**
4. Set username, full name, password, and role
5. Click **Save User**

Available roles: `admin`, `anesthesiologist`, `surgeon`, `staff`

---

## How other devices connect

While the server is running, find the **LAN IP** displayed in the terminal
(e.g. `http://192.168.1.100:8100`) or check the login page banner.

To find the host computer's IP manually:

**Mac:**
```bash
ipconfig getifaddr en0
```

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under Wi-Fi adapter.

**Linux:**
```bash
hostname -I
```

On any other device (phone, tablet, another computer) connected to the
**same Wi-Fi**, open a browser and type:
```
http://192.168.x.x:8100
```
replacing `192.168.x.x` with the host computer's IP.

> The host computer must be on and the server must be running for others to connect.

---

## Backup & restore

### From the web interface (easiest)

1. Log in as **admin**
2. Click **☰ menu → Backup / Restore** in the sidebar
3. **Download Backup** — saves a `.db` file to your computer
4. **Restore** — upload a `.db` backup file to replace the current database

### From the command line

**Backup:**
```bash
bash scripts/backup.sh               # saves to current folder
bash scripts/backup.sh /Volumes/USB  # saves to USB drive
```

**Restore** (stop the server first):
```bash
bash scripts/restore.sh /path/to/vetanesthesia_backup_20260612_120000.db
```

### What is backed up

The single `.db` file contains **everything**:
- All patient records
- All anesthetic records
- Monitoring logs, drug entries, fluid entries
- Emergency drug/event logs
- User accounts
- Exported report history

Exported PDF/DOCX files are in the `exports/` folder (back these up separately
if you want to keep previous exports).

### Automatic safety backup before restore

Before any restore operation, the system automatically copies the current
database to `anesthesia.db.pre_restore_TIMESTAMP` so you can undo if needed.

---

## Transferring to another computer

To move the entire app and all its data to a new host computer:

1. **Stop the server** on the old computer
2. **Backup the database**: `bash scripts/backup.sh`
3. **Copy** the entire `vet-anesthesia` folder to the new computer
   (include the `data/` folder if using Docker, or `anesthesia.db` if manual)
4. **Install** on the new computer (see Option A or B above)
5. **Start** the app on the new computer
6. Other devices can now connect to the **new computer's IP address**

---

## Stopping the server

**Docker:**
```bash
docker compose down
```

**Manual (start.sh):**
Press `Ctrl+C` in the terminal window running the server.

---

## Changing the port

**Docker** — edit `docker-compose.yml`:
```yaml
ports:
  - "9000:8100"   # Access on port 9000 instead of 8100
```
Then restart: `docker compose down && docker compose up -d`

**Manual:**
```bash
PORT=9000 bash start.sh
```

---

## Troubleshooting

### "Connection refused" from another device
- Make sure the server is running (`docker compose ps` or check terminal)
- Confirm both devices are on the **same Wi-Fi network**
- Try turning off the Windows Firewall temporarily to test
- On Mac, check System Settings → Firewall

### Port 8100 already in use
```bash
PORT=8200 bash start.sh          # manual
# Or change the port in docker-compose.yml
```

### Docker: "cannot connect to Docker daemon"
Make sure Docker Desktop is open and shows "Engine running".

### Export PDF/DOCX fails
Run `pip3 install reportlab python-docx matplotlib` to ensure all export
libraries are installed.

### Database not found after moving to new computer
Make sure you copied `anesthesia.db` (manual install) or the `data/` folder
(Docker install) along with the app files.

### Reset to factory defaults
Delete `anesthesia.db` (or `data/anesthesia.db`) and restart the server.
A fresh database with default admin/admin1234 will be created automatically.
**This deletes all patient records permanently.**
