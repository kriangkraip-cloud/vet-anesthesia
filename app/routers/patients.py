from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from .. import models, auth, schemas

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=List[dict])
async def list_patients(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Patient)
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                models.Patient.hn.ilike(search),
                models.Patient.name.ilike(search),
                models.Patient.species.ilike(search),
                models.Patient.owner_name.ilike(search),
            )
        )
    patients = query.order_by(models.Patient.created_at.desc()).all()

    result = []
    for p in patients:
        latest_record = (
            db.query(models.AnestheticRecord)
            .filter(models.AnestheticRecord.patient_id == p.id)
            .order_by(models.AnestheticRecord.record_date.desc())
            .first()
        )
        result.append({
            "id": p.id,
            "hn": p.hn,
            "name": p.name,
            "species": p.species,
            "breed": p.breed,
            "sex": p.sex,
            "age": p.age,
            "weight": p.weight,
            "owner_name": p.owner_name,
            "record_id": latest_record.id if latest_record else None,
            "record_date": latest_record.record_date.isoformat() if latest_record and latest_record.record_date else None,
            "surgical_procedure": latest_record.surgical_procedure if latest_record else None,
            "surgeon": latest_record.surgeon if latest_record else None,
            "anesthesiologist": latest_record.anesthesiologist if latest_record else None,
            "status": latest_record.status if latest_record else None,
            "record_count": db.query(models.AnestheticRecord).filter(models.AnestheticRecord.patient_id == p.id).count(),
        })
    return result


@router.get("/{patient_id}", response_model=schemas.PatientOut)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("", response_model=schemas.PatientOut)
async def create_patient(
    data: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if db.query(models.Patient).filter(models.Patient.hn == data.hn).first():
        raise HTTPException(status_code=400, detail="HN already exists")
    patient = models.Patient(**data.model_dump(), created_by_id=current_user.id, updated_by_id=current_user.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=schemas.PatientOut)
async def update_patient(
    patient_id: int,
    data: schemas.PatientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(patient, field, value)
    patient.updated_by_id = current_user.id
    patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(patient)
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin access required")
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"ok": True}
