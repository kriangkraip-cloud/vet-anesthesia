import os
import shutil
import tempfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from .. import models, auth
from ..database import DB_PATH, engine

router = APIRouter(prefix="/api/backup", tags=["backup"])


def _admin_only(current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


@router.get("/download")
async def download_backup(_: models.User = Depends(_admin_only)):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file not found")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vetanesthesia_backup_{ts}.db"
    return FileResponse(
        DB_PATH,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    _: models.User = Depends(_admin_only),
):
    if not (file.filename or "").endswith(".db"):
        raise HTTPException(status_code=400, detail="File must be a .db backup file")

    content = await file.read()

    if not content.startswith(b"SQLite format 3"):
        raise HTTPException(status_code=400, detail="Not a valid SQLite database file")

    # Save current DB as a pre-restore backup
    if os.path.exists(DB_PATH):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DB_PATH, DB_PATH + f".pre_restore_{ts}")

    # Write the restored database
    with open(DB_PATH, "wb") as f:
        f.write(content)

    # Dispose SQLAlchemy engine so new connections pick up the restored file
    engine.dispose()

    # Run schema migrations on the restored DB so old backups get all newer columns
    try:
        from sqlalchemy import text
        from ..database import Base
        Base.metadata.create_all(bind=engine)
        _RESTORE_MIGRATIONS = [
            ("monitoring_entries", "fluid_rate",         "FLOAT"),
            ("anesthetic_records", "procedure_notes",    "TEXT"),
            ("anesthetic_records", "sample_collection",  "TEXT"),
            ("anesthetic_records", "postop_medications", "TEXT"),
            ("surgeon_duties",     "repeat_group_id",    "VARCHAR(36)"),
            ("patients",           "owner_phone",        "VARCHAR(20)"),
        ]
        with engine.connect() as conn:
            for table, col, col_type in _RESTORE_MIGRATIONS:
                try:
                    result = conn.execute(text(f"PRAGMA table_info({table})"))
                    if col not in {r[1] for r in result.fetchall()}:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
            try:
                conn.execute(text("UPDATE anesthetic_records SET status='waiting' WHERE status='draft'"))
                conn.execute(text("UPDATE anesthetic_records SET status='complete' WHERE status IN ('completed','exported')"))
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
    except Exception:
        pass

    return JSONResponse({"message": "Database restored successfully. Refresh the page to see updated data."})


@router.get("/info")
async def backup_info(_: models.User = Depends(_admin_only)):
    size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    mtime = os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "db_path": DB_PATH,
        "size_bytes": size,
        "size_kb": round(size / 1024, 1),
        "last_modified": datetime.fromtimestamp(mtime).isoformat() if mtime else None,
    }
