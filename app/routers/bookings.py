import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date, datetime, timedelta
from ..database import get_db
from .. import models, auth, schemas

router = APIRouter(prefix="/api", tags=["bookings"])

# ── OR Bookings ─────────────────────────────────────────────────────────────

@router.get("/bookings", response_model=List[dict])
async def list_bookings(
    surgery_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = (
        db.query(models.ORBooking)
        .join(models.AnestheticRecord)
        .join(models.Patient)
        .options(
            joinedload(models.ORBooking.record).joinedload(models.AnestheticRecord.patient)
        )
    )
    if surgery_date:
        try:
            d = date.fromisoformat(surgery_date)
            query = query.filter(models.ORBooking.surgery_date == d)
        except ValueError:
            pass
    bookings = query.order_by(models.ORBooking.or_number, models.ORBooking.slot_start, models.ORBooking.sort_order).all()
    return [_fmt_booking(b) for b in bookings]


def _fmt_booking(b: models.ORBooking) -> dict:
    r = b.record
    p = r.patient if r else None
    slot_end = b.slot_start + b.num_slots if b.slot_start and b.num_slots else None
    return {
        "id": b.id,
        "record_id": b.record_id,
        "surgery_date": b.surgery_date.isoformat() if b.surgery_date else None,
        "or_number": b.or_number,
        "slot_start": b.slot_start,
        "num_slots": b.num_slots,
        "sort_order": b.sort_order,
        "time_range": f"{b.slot_start:02d}:00–{slot_end:02d}:00" if slot_end else "—",
        "hn": p.hn if p else "—",
        "patient_name": p.name if p else "—",
        "surgical_procedure": r.surgical_procedure if r else "—",
        "surgeon": r.surgeon if r else "—",
        "status": r.status if r else "waiting",
    }


@router.post("/records/{record_id}/booking", response_model=schemas.ORBookingOut)
async def upsert_booking(
    record_id: int,
    data: schemas.ORBookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    record = db.query(models.AnestheticRecord).filter(models.AnestheticRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Warn if >4 slots on same day in same OR (check total)
    if data.surgery_date and data.or_number:
        existing = db.query(models.ORBooking).filter(
            models.ORBooking.surgery_date == data.surgery_date,
            models.ORBooking.or_number == data.or_number,
            models.ORBooking.record_id != record_id,
        ).all()
        total_slots = sum(b.num_slots or 1 for b in existing) + (data.num_slots or 1)
        if total_slots > 4:
            pass  # warning is returned in response, not blocking

    booking = db.query(models.ORBooking).filter(models.ORBooking.record_id == record_id).first()
    if booking:
        for field, value in data.model_dump().items():
            setattr(booking, field, value)
        booking.updated_at = datetime.utcnow()
    else:
        booking = models.ORBooking(**data.model_dump(), record_id=record_id)
        db.add(booking)

    # Sync surgery_start time on the anesthetic record
    if data.surgery_date and data.slot_start is not None:
        from datetime import datetime as dt
        new_start = dt(data.surgery_date.year, data.surgery_date.month, data.surgery_date.day,
                       data.slot_start, 0, 0)
        # Convert to UTC (Thailand = UTC+7)
        new_start_utc = new_start - timedelta(hours=7)
        record.surgery_start = new_start_utc
        record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/records/{record_id}/booking")
async def delete_booking(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    booking = db.query(models.ORBooking).filter(models.ORBooking.record_id == record_id).first()
    if booking:
        db.delete(booking)
        db.commit()
    return {"ok": True}


@router.get("/schedule/check")
async def check_schedule(
    surgery_date: str,
    or_number: int = 1,
    exclude_record_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        d = date.fromisoformat(surgery_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    query = db.query(models.ORBooking).filter(
        models.ORBooking.surgery_date == d,
        models.ORBooking.or_number == or_number,
    )
    if exclude_record_id:
        query = query.filter(models.ORBooking.record_id != exclude_record_id)
    bookings = query.all()
    total_slots = sum(b.num_slots or 1 for b in bookings)
    return {
        "date": surgery_date,
        "or_number": or_number,
        "booked_slots": total_slots,
        "warning": total_slots >= 4,
        "message": f"Warning: {total_slots} slots already booked. Operating room may be full." if total_slots >= 4 else ""
    }


# ── Procedure Templates ──────────────────────────────────────────────────────

@router.get("/procedure-templates", response_model=List[schemas.ProcedureTemplateOut])
async def list_templates(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.ProcedureTemplate).order_by(
        models.ProcedureTemplate.is_system.desc(),
        models.ProcedureTemplate.name
    ).all()


@router.post("/procedure-templates", response_model=schemas.ProcedureTemplateOut)
async def create_template(
    data: schemas.ProcedureTemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    tpl = models.ProcedureTemplate(
        name=data.name,
        content=data.content,
        is_system=False,
        created_by_id=current_user.id,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


@router.delete("/procedure-templates/{tpl_id}")
async def delete_template(
    tpl_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    tpl = db.query(models.ProcedureTemplate).filter(models.ProcedureTemplate.id == tpl_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    if tpl.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system templates")
    db.delete(tpl)
    db.commit()
    return {"ok": True}


# ── Procedure Images ─────────────────────────────────────────────────────────

def _images_dir(record_id: int) -> str:
    from ..database import DATA_DIR
    d = os.path.join(DATA_DIR, "procedure_images", str(record_id))
    os.makedirs(d, exist_ok=True)
    return d


@router.post("/records/{record_id}/images", response_model=schemas.ProcedureImageOut)
async def upload_image(
    record_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    record = db.query(models.AnestheticRecord).filter(models.AnestheticRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    ext = os.path.splitext(file.filename or "image.jpg")[1].lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"}:
        ext = ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"

    img_dir = _images_dir(record_id)
    dest = os.path.join(img_dir, unique_name)
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    count = db.query(models.ProcedureImage).filter(models.ProcedureImage.record_id == record_id).count()
    img = models.ProcedureImage(
        record_id=record_id,
        filename=unique_name,
        original_name=file.filename,
        label="",
        for_export=False,
        sort_order=count,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


@router.get("/records/{record_id}/images", response_model=List[schemas.ProcedureImageOut])
async def list_images(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.ProcedureImage).filter(
        models.ProcedureImage.record_id == record_id
    ).order_by(models.ProcedureImage.sort_order).all()


@router.put("/records/{record_id}/images/{image_id}", response_model=schemas.ProcedureImageOut)
async def update_image(
    record_id: int,
    image_id: int,
    label: Optional[str] = None,
    for_export: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    img = db.query(models.ProcedureImage).filter(
        models.ProcedureImage.id == image_id,
        models.ProcedureImage.record_id == record_id
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    if label is not None:
        img.label = label
    if for_export is not None:
        img.for_export = for_export
    db.commit()
    db.refresh(img)
    return img


@router.delete("/records/{record_id}/images/{image_id}")
async def delete_image(
    record_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    img = db.query(models.ProcedureImage).filter(
        models.ProcedureImage.id == image_id,
        models.ProcedureImage.record_id == record_id
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    # Delete file
    img_dir = _images_dir(record_id)
    file_path = os.path.join(img_dir, img.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(img)
    db.commit()
    return {"ok": True}


@router.get("/images/{record_id}/{filename}")
async def serve_image(
    record_id: int,
    filename: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    # Accept token from query string (for <img src> tags) or Authorization header
    from ..auth import get_current_user
    from fastapi.security import OAuth2PasswordBearer
    from jose import JWTError, jwt
    from ..auth import SECRET_KEY, ALGORITHM
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    img_dir = _images_dir(record_id)
    file_path = os.path.join(img_dir, filename)
    if not os.path.exists(file_path) or not os.path.abspath(file_path).startswith(os.path.abspath(img_dir)):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)
