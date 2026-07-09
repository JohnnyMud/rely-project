from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Patients
from app.schemas import PatientCreate, PatientResponse
from app.logic.patient_manager import create_patient

router = APIRouter(tags=["patients"])

@router.get("/patients", response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patients).all()
    return patients

@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient_record(patient: PatientCreate, db: Session = Depends(get_db)):
    return create_patient(db, patient)


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_record(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patients).filter(Patients.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    db.delete(patient)
    db.commit()
