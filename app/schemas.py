from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    date_of_birth: date = Field(alias="dateOfBirth")
    phone_number: str = Field(alias="phoneNumber")
    home_address: str = Field(alias="homeAddress")
    insurance_number: str = Field(alias="insuranceNumber")
    medical_record_number: str = Field(alias="medicalRecordNumber")
    appointment_date: date = Field(alias="appointmentDate")
    appointment_time: time = Field(alias="appointmentTime")
    timezone: str


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone_number: str
    home_address: str
    insurance_number: str
    medical_record_number: str
    appointment_date: date
    appointment_time: time
    timezone: str
