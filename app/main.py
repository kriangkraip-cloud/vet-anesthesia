import os
import socket
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from .database import engine, Base
from . import models
from .auth import get_password_hash
from .database import SessionLocal
from .routers import auth, users, patients, records, export, backup


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

# Serve static files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def run_migrations():
    from sqlalchemy import text
    db = SessionLocal()
    try:
        try:
            db.execute(text("ALTER TABLE monitoring_entries ADD COLUMN fluid_rate FLOAT"))
            db.commit()
        except Exception:
            pass  # Column already exists
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
