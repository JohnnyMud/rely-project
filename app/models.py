from datetime import date, time, datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Patients(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[date]
    phone_number: Mapped[str]
    home_address: Mapped[str]
    insurance_number: Mapped[str]
    medical_record_number: Mapped[str]
    appointment_date: Mapped[date]
    appointment_time: Mapped[time]
    timezone: Mapped[str]

    calls: Mapped[list["CallAttempts"]] = relationship(back_populates="patient")

class CallAttempts(Base):
    __tablename__ = "calls"

    call_attempt_id: Mapped[str] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    retell_call_id: Mapped[str]
    created_at: Mapped[datetime]
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime]
    call_duration: Mapped[int]
    call_status: Mapped[str]
    successful: Mapped[bool]
    recording_url: Mapped[str]
    summary: Mapped[str] = mapped_column(Text)

    patient: Mapped["Patients"] = relationship(back_populates="calls")