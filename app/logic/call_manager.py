import os
from datetime import datetime

from retell import Retell
from sqlalchemy.orm import Session

from app.models import CallAttempts, Patients

retell_client = Retell(
    api_key=os.getenv("RETELL_API_KEY")
)

def initiate_retell_call(patient_number: str):
    try:
        response = retell_client.call.create_phone_call(
            from_number="+14157499804",
            to_number=patient_number
        )
        print(f"Call initiated: {response}")
        return response
    except Exception as e:
        print(f"Error making call: {e}")
        return False

def create_call_attempt(patient_id: str, db: Session):
    record = CallAttempts(
        patient_id=patient_id,
        call_date=datetime.now(),
        call_time=datetime.now().time(),
        call_duration=0,
        call_type="phone",
        call_status="pending"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def call_patient(patient: Patients, db: Session):
    patient_id = patient.id
    call_attempt = create_call_attempt(patient_id, db)
    call_succeeded = initiate_retell_call(patient.phone_number)
    retell_call_id = call_succeeded.call_id
    call_attempt.call_status = "initiated"

    if not call_succeeded:
        call_attempt.call_status = "failed"
        db.commit()
        db.refresh(call_attempt)

    return call_attempt