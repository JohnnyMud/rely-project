from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import CallAttempts, Patients
from app.db import get_db
from app.logic.call_manager import call_patient

router = APIRouter()

@router.post("/patients/{patient_id}/calls", status_code=status.HTTP_201_CREATED)
def create_call(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patients).filter(Patients.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    call_attempt = call_patient(patient, db)
    return call_attempt

@router.get("/patients/{patient_id}/calls")
def get_calls(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patients).filter(Patients.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    call_history = (db.query(CallAttempts)
    .filter(CallAttempts.patient_id == patient_id)
    .order_by(CallAttempts.created_at.desc())
    .all()
    )
    return call_history