from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Patients
from app.schemas import PatientCreate, PatientResponse
from app.logic.patient_manager import create_patient

router = APIRouter()

@router.get("/patients", response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patients).all()
    return patients

@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient_record(patient: PatientCreate, db: Session = Depends(get_db)):
    return create_patient(db, patient)
