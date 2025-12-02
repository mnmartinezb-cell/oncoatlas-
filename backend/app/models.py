from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    specialty = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Un médico puede tener muchos pacientes
    patients = relationship(
        "Patient",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    document_number = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con médico
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    doctor = relationship("Doctor", back_populates="patients")

    # Relación con análisis germinales
    analyses = relationship(
        "GermlineAnalysis",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class GermlineAnalysis(Base):
    __tablename__ = "germline_analyses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    description = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    # JSON con el resultado completo del análisis (variants, summary, etc.)
    raw_result = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="analyses")


