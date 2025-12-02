from typing import Optional

from pydantic import BaseModel


class PatientBase(BaseModel):
    full_name: str
    document_number: str
    age: Optional[int] = None
    gender: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    id: int

    class Config:
        orm_mode = True  # permite convertir desde objetos SQLAlchemy
