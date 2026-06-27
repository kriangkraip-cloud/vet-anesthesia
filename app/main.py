import os
import socket
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from .database import engine, Base
from . import models
from .auth import get_password_hash
from .database import SessionLocal
from .routers import auth, users, patients, records, export, backup, bookings


def _get_lan_ip() -> str:
    try:
        import subprocess
        for iface in ("en0", "en1"):
            r = subprocess.run(["ipconfig", "getifaddr", iface], capture_output=True, text=True)
            ip = r.stdout.strip()
            if ip:
                return ip
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vet Anesthesia Records", version="1.0.0")

# Register API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(records.router)
app.include_router(export.router)
app.include_router(backup.router)
app.include_router(bookings.router)

# Serve static files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def run_migrations():
    from sqlalchemy import text

    # Use direct engine connection with explicit checks to avoid transaction issues
    with engine.connect() as conn:
        def col_exists(table: str, col: str) -> bool:
            rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            return any(r[1] == col for r in rows)

        def tbl_exists(table: str) -> bool:
            r = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
            ), {"t": table}).fetchone()
            return r is not None

        column_migrations = [
            ("monitoring_entries",  "fluid_rate",       "FLOAT"),
            ("anesthetic_records",  "procedure_notes",  "TEXT"),
            ("anesthetic_records",  "sample_collection","TEXT"),
            ("anesthetic_records",  "postop_medications","TEXT"),
            ("surgeon_duties",      "repeat_group_id",  "VARCHAR(36)"),
            ("patients",            "owner_phone",      "VARCHAR(20)"),
        ]

        for table, col, col_type in column_migrations:
            if tbl_exists(table) and not col_exists(table, col):
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()
                    print(f"✓ Migration: added {table}.{col}")
                except Exception as e:
                    print(f"✗ Migration warning ({table}.{col}): {e}")

        # Migrate old status values
        try:
            conn.execute(text("UPDATE anesthetic_records SET status='waiting' WHERE status='draft'"))
            conn.execute(text("UPDATE anesthetic_records SET status='complete' WHERE status IN ('completed','exported')"))
            conn.commit()
        except Exception:
            pass


@app.on_event("startup")
async def seed_procedure_templates():
    db = SessionLocal()
    try:
        if db.query(models.ProcedureTemplate).filter(models.ProcedureTemplate.is_system == True).count() == 0:
            system_templates = [
                models.ProcedureTemplate(
                    name="Castration (Male)",
                    content=(
                        "Incision: prescrotal / scrotal approach, length ____ cm\n"
                        "Left testis delivered, spermatic cord: clamped, ligated (2-0 Vicryl), transected\n"
                        "Right testis: same technique\n"
                        "Hemostasis confirmed\n"
                        "Closure: subcutaneous 3-0 Monocryl, skin 3-0 Nylon / tissue glue\n"
                        "Intraoperative findings: ____"
                    ),
                    is_system=True,
                ),
                models.ProcedureTemplate(
                    name="OVH (Spay)",
                    content=(
                        "Midline incision from umbilicus, length ____ cm\n"
                        "Linea alba incised, abdominal cavity entered\n"
                        "Right ovary: proper ligament transected, pedicle double-ligated (2-0 Vicryl), transected\n"
                        "Left ovary: same technique\n"
                        "Uterine body: clamped, transfixed ligation, transected proximal to cervix\n"
                        "Hemostasis confirmed, peritoneal lavage: No / Yes (____)\n"
                        "Closure: linea alba 2-0 PDS continuous, subcutaneous 3-0 Monocryl, skin sutures / staples\n"
                        "Intraoperative findings: ____"
                    ),
                    is_system=True,
                ),
                models.ProcedureTemplate(
                    name="Skin Mass Removal",
                    content=(
                        "Mass location: ____  Size: ____ × ____ cm  Consistency: ____\n"
                        "Planned excision margin: ____ cm\n"
                        "Elliptical incision with ____ cm margins\n"
                        "Blunt and sharp dissection to base\n"
                        "Hemostasis: electrocautery / ligation\n"
                        "Specimen submitted for histopathology: Yes / No\n"
                        "Wound closure:\n"
                        "  Deep: ____\n"
                        "  Subcutaneous: 3-0 Monocryl\n"
                        "  Skin: ____ sutures / staples\n"
                        "Closure tension: minimal / moderate / high\n"
                        "Intraoperative findings: ____"
                    ),
                    is_system=True,
                ),
            ]
            for t in system_templates:
                db.add(t)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
async def seed_drug_presets():
    db = SessionLocal()
    try:
        if db.query(models.DrugPreset).filter(models.DrugPreset.is_system == True).count() == 0:
            defaults = [
                # (drug_name, concentration, concentration_unit, dose_unit)
                ("midazolam",            5,      "mg/mL",  "mg/kg"),
                ("diazepam",             5,      "mg/mL",  "mg/kg"),
                ("acepromazine",         10,     "mg/mL",  "mg/kg"),
                ("xylazine",             20,     "mg/mL",  "mg/kg"),
                ("medetomidine",         1,      "mg/mL",  "mcg/kg"),
                ("dexmedetomidine",      0.5,    "mg/mL",  "mcg/kg"),
                ("ketamine",             50,     "mg/mL",  "mg/kg"),
                ("propofol",             10,     "mg/mL",  "mg/kg"),
                ("alfaxalone",           10,     "mg/mL",  "mg/kg"),
                ("etomidate",            2,      "mg/mL",  "mg/kg"),
                ("lidocaine",            20,     "mg/mL",  "mg/kg"),
                ("bupivacaine",          5,      "mg/mL",  "mg/kg"),
                ("ropivacaine",          2,      "mg/mL",  "mg/kg"),
                ("morphine",             10,     "mg/mL",  "mg/kg"),
                ("fentanyl",             0.05,   "mg/mL",  "mcg/kg"),
                ("buprenorphine",        0.3,    "mg/mL",  "mcg/kg"),
                ("butorphanol",          10,     "mg/mL",  "mg/kg"),
                ("tramadol",             50,     "mg/mL",  "mg/kg"),
                ("meloxicam",            5,      "mg/mL",  "mg/kg"),
                ("carprofen",            50,     "mg/mL",  "mg/kg"),
                ("atropine",             0.6,    "mg/mL",  "mg/kg"),
                ("glycopyrrolate",       0.2,    "mg/mL",  "mg/kg"),
                ("neostigmine",          0.5,    "mg/mL",  "mg/kg"),
                ("epinephrine",          1,      "mg/mL",  "mcg/kg"),
                ("dopamine",             40,     "mg/mL",  "mcg/kg/min"),
                ("dobutamine",           12.5,   "mg/mL",  "mcg/kg/min"),
                ("furosemide",           10,     "mg/mL",  "mg/kg"),
                ("maropitant",           10,     "mg/mL",  "mg/kg"),
                ("metoclopramide",       5,      "mg/mL",  "mg/kg"),
                ("dexamethasone",        4,      "mg/mL",  "mg/kg"),
            ]
            for i, (name, conc, conc_unit, dose_unit) in enumerate(defaults):
                db.add(models.DrugPreset(
                    drug_name=name,
                    concentration=conc,
                    concentration_unit=conc_unit,
                    dose_unit=dose_unit,
                    is_system=True,
                    sort_order=i,
                ))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
async def create_default_admin():
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.username == "admin").first():
            admin = models.User(
                username="admin",
                email="admin@vetanesthesia.local",
                full_name="Administrator",
                hashed_password=get_password_hash("admin1234"),
                role="admin",
            )
            db.add(admin)
            # Demo staff user
            staff = models.User(
                username="anesthesiologist",
                email="anes@vetanesthesia.local",
                full_name="Dr. Anesthesiologist",
                hashed_password=get_password_hash("anes1234"),
                role="anesthesiologist",
            )
            db.add(staff)
            db.commit()
            print("✓ Default users created: admin/admin1234 | anesthesiologist/anes1234")
    finally:
        db.close()


_NO_CACHE = {"Cache-Control": "no-store, no-cache, must-revalidate"}


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "pages", "login.html"), headers=_NO_CACHE)


@app.get("/dashboard")
async def dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "pages", "dashboard.html"), headers=_NO_CACHE)


@app.get("/patient")
async def patient_page():
    return FileResponse(os.path.join(STATIC_DIR, "pages", "patient.html"), headers=_NO_CACHE)


@app.get("/record")
async def record_page():
    return FileResponse(os.path.join(STATIC_DIR, "pages", "record.html"), headers=_NO_CACHE)


@app.get("/api/server-info")
async def server_info():
    lan_ip = _get_lan_ip()
    return JSONResponse({"lan_ip": lan_ip, "port": int(os.environ.get("PORT", 8100))})
