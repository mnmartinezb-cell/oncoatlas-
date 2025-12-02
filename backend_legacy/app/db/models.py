from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    specialty = Column(String, nullable=True)

    patients = relationship("Patient", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    document_number = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)

    doctor = relationship("Doctor", back_populates="patients")
    analyses = relationship("GermlineAnalysis", back_populates="patient")


class GermlineAnalysis(Base):
    __tablename__ = "germline_analyses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True, nullable=False)

    description = Column(String, nullable=False, default="Análisis germinal BRCA1/BRCA2")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Resumen corto que mostraremos en la tabla
    summary = Column(String, nullable=True)

    # JSON completo del resultado del análisis
    raw_result = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="analyses")

