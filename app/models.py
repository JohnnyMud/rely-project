import uuid
from datetime import date, time, datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Patients(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
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

    calls: Mapped[list["CallAttempts"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )

class CallAttempts(Base):
    __tablename__ = "calls"

    call_attempt_id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"))
    retell_call_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime]
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    call_duration: Mapped[int | None] = mapped_column(nullable=True)
    call_status: Mapped[str]
    successful: Mapped[bool | None] = mapped_column(nullable=True)
    recording_url: Mapped[str | None] = mapped_column(nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["Patients"] = relationship(back_populates="calls")