from sqlalchemy.orm import Session
from app.schemas import PatientCreate
from app.models import Patients

def create_patient(db: Session, patient: PatientCreate) -> Patients:
    record = Patients(**patient.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record