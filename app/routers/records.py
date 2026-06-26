from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from .. import models, auth, schemas

router = APIRouter(prefix="/api/records", tags=["records"])


# ── Anesthetic Records ──────────────────────────────────────────────────────

@router.get("", response_model=List[dict])
async def list_records(
    q: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = (
        db.query(models.AnestheticRecord)
        .join(models.Patient)
        .options(joinedload(models.AnestheticRecord.patient))
    )
    if patient_id:
        query = query.filter(models.AnestheticRecord.patient_id == patient_id)
    if status:
        query = query.filter(models.AnestheticRecord.status == status)
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                models.Patient.hn.ilike(search),
                models.Patient.name.ilike(search),
                models.Patient.species.ilike(search),
                models.AnestheticRecord.surgeon.ilike(search),
                models.AnestheticRecord.anesthesiologist.ilike(search),
                models.AnestheticRecord.surgical_procedure.ilike(search),
            )
        )
    records = query.order_by(models.AnestheticRecord.record_date.desc()).all()
    return [_format_record_summary(r) for r in records]


def _format_record_summary(r: models.AnestheticRecord) -> dict:
    return {
        "id": r.id,
        "patient_id": r.patient_id,
        "hn": r.patient.hn,
        "patient_name": r.patient.name,
        "species": r.patient.species,
        "record_date": r.record_date.isoformat() if r.record_date else None,
        "surgeon": r.surgeon,
        "anesthesiologist": r.anesthesiologist,
        "surgical_procedure": r.surgical_procedure,
        "status": r.status,
        "anesthesia_start": r.anesthesia_start.isoformat() if r.anesthesia_start else None,
        "anesthesia_end": r.anesthesia_end.isoformat() if r.anesthesia_end else None,
    }


@router.get("/{record_id}", response_model=schemas.RecordOut)
async def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    record = _load_full_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


def _load_full_record(db: Session, record_id: int):
    return (
        db.query(models.AnestheticRecord)
        .options(
            joinedload(models.AnestheticRecord.drug_entries),
            joinedload(models.AnestheticRecord.monitoring_entries),
            joinedload(models.AnestheticRecord.fluid_entries),
            joinedload(models.AnestheticRecord.emergency_events),
            joinedload(models.AnestheticRecord.surgical_procedures),
            joinedload(models.AnestheticRecord.or_booking),
            joinedload(models.AnestheticRecord.procedure_images),
        )
        .filter(models.AnestheticRecord.id == record_id)
        .first()
    )


@router.post("", response_model=schemas.RecordOut)
async def create_record(
    data: schemas.RecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(models.Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    record_data = data.model_dump()
    record_data["record_date"] = data.record_date or date.today()
    record = models.AnestheticRecord(
        **record_data,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(record)
    db.commit()
    return _load_full_record(db, record.id)


@router.put("/{record_id}", response_model=schemas.RecordOut)
async def update_record(
    record_id: int,
    data: schemas.RecordUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    record = db.query(models.AnestheticRecord).filter(models.AnestheticRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(record, field, value)
    record.updated_by_id = current_user.id
    record.updated_at = datetime.utcnow()
    db.commit()
    return _load_full_record(db, record_id)


@router.delete("/{record_id}")
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin access required")
    record = db.query(models.AnestheticRecord).filter(models.AnestheticRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"ok": True}


# ── Drug Entries ────────────────────────────────────────────────────────────

@router.get("/{record_id}/drugs", response_model=List[schemas.DrugEntryOut])
async def list_drugs(record_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    return db.query(models.DrugEntry).filter(models.DrugEntry.record_id == record_id).order_by(models.DrugEntry.sort_order).all()


@router.post("/{record_id}/drugs", response_model=schemas.DrugEntryOut)
async def add_drug(record_id: int, data: schemas.DrugEntryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    entry = models.DrugEntry(**data.model_dump(), record_id=record_id, created_by_id=current_user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{record_id}/drugs/{entry_id}", response_model=schemas.DrugEntryOut)
async def update_drug(record_id: int, entry_id: int, data: schemas.DrugEntryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = _require_drug(db, record_id, entry_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{record_id}/drugs/{entry_id}")
async def delete_drug(record_id: int, entry_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = _require_drug(db, record_id, entry_id)
    db.delete(entry)
    db.commit()
    return {"ok": True}


# ── Monitoring ──────────────────────────────────────────────────────────────

@router.get("/{record_id}/monitoring", response_model=List[schemas.MonitoringEntryOut])
async def list_monitoring(record_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    return db.query(models.MonitoringEntry).filter(models.MonitoringEntry.record_id == record_id).order_by(models.MonitoringEntry.time).all()


@router.post("/{record_id}/monitoring", response_model=schemas.MonitoringEntryOut)
async def add_monitoring(record_id: int, data: schemas.MonitoringEntryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    entry = models.MonitoringEntry(**data.model_dump(), record_id=record_id, created_by_id=current_user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{record_id}/monitoring/{entry_id}", response_model=schemas.MonitoringEntryOut)
async def update_monitoring(record_id: int, entry_id: int, data: schemas.MonitoringEntryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.MonitoringEntry).filter(models.MonitoringEntry.id == entry_id, models.MonitoringEntry.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{record_id}/monitoring/{entry_id}")
async def delete_monitoring(record_id: int, entry_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.MonitoringEntry).filter(models.MonitoringEntry.id == entry_id, models.MonitoringEntry.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}


# ── Fluids ──────────────────────────────────────────────────────────────────

@router.get("/{record_id}/fluids", response_model=List[schemas.FluidEntryOut])
async def list_fluids(record_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    return db.query(models.FluidEntry).filter(models.FluidEntry.record_id == record_id).order_by(models.FluidEntry.sort_order).all()


@router.post("/{record_id}/fluids", response_model=schemas.FluidEntryOut)
async def add_fluid(record_id: int, data: schemas.FluidEntryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    entry = models.FluidEntry(**data.model_dump(), record_id=record_id, created_by_id=current_user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{record_id}/fluids/{entry_id}", response_model=schemas.FluidEntryOut)
async def update_fluid(record_id: int, entry_id: int, data: schemas.FluidEntryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.FluidEntry).filter(models.FluidEntry.id == entry_id, models.FluidEntry.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{record_id}/fluids/{entry_id}")
async def delete_fluid(record_id: int, entry_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.FluidEntry).filter(models.FluidEntry.id == entry_id, models.FluidEntry.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}


# ── Emergency Events ────────────────────────────────────────────────────────

@router.get("/{record_id}/emergency", response_model=List[schemas.EmergencyEventOut])
async def list_emergency(record_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    return db.query(models.EmergencyEvent).filter(models.EmergencyEvent.record_id == record_id).order_by(models.EmergencyEvent.time).all()


@router.post("/{record_id}/emergency", response_model=schemas.EmergencyEventOut)
async def add_emergency(record_id: int, data: schemas.EmergencyEventCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    entry = models.EmergencyEvent(**data.model_dump(), record_id=record_id, created_by_id=current_user.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{record_id}/emergency/{entry_id}", response_model=schemas.EmergencyEventOut)
async def update_emergency(record_id: int, entry_id: int, data: schemas.EmergencyEventCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.EmergencyEvent).filter(models.EmergencyEvent.id == entry_id, models.EmergencyEvent.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{record_id}/emergency/{entry_id}")
async def delete_emergency(record_id: int, entry_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.EmergencyEvent).filter(models.EmergencyEvent.id == entry_id, models.EmergencyEvent.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}


# ── Surgical Procedures ─────────────────────────────────────────────────────

@router.get("/{record_id}/procedures", response_model=List[schemas.SurgicalProcedureOut])
async def list_procedures(record_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    return db.query(models.SurgicalProcedure).filter(models.SurgicalProcedure.record_id == record_id).order_by(models.SurgicalProcedure.sort_order).all()


@router.post("/{record_id}/procedures", response_model=schemas.SurgicalProcedureOut)
async def add_procedure(record_id: int, data: schemas.SurgicalProcedureCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    _require_record(db, record_id)
    entry = models.SurgicalProcedure(**data.model_dump(), record_id=record_id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{record_id}/procedures/{entry_id}", response_model=schemas.SurgicalProcedureOut)
async def update_procedure(record_id: int, entry_id: int, data: schemas.SurgicalProcedureCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.SurgicalProcedure).filter(models.SurgicalProcedure.id == entry_id, models.SurgicalProcedure.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{record_id}/procedures/{entry_id}")
async def delete_procedure(record_id: int, entry_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    entry = db.query(models.SurgicalProcedure).filter(models.SurgicalProcedure.id == entry_id, models.SurgicalProcedure.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _require_record(db: Session, record_id: int) -> models.AnestheticRecord:
    record = db.query(models.AnestheticRecord).filter(models.AnestheticRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


def _require_drug(db: Session, record_id: int, entry_id: int) -> models.DrugEntry:
    entry = db.query(models.DrugEntry).filter(models.DrugEntry.id == entry_id, models.DrugEntry.record_id == record_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Drug entry not found")
    return entry
