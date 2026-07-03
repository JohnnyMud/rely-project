from datetime import date, time

from sqlalchemy import Date, String, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
