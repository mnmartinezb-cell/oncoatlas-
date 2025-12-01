# backend/app/models.py
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    specialty = Column(String(200), nullable=True)
    is_admin = Column(Boolean, default=False)

    patients = relationship("Patient", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    document_id = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    sex = Column(String(10), nullable=False)

    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    doctor = relationship("Doctor", back_populates="patients")

    analyses = relationship("Analysis", back_populates="patient")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="COMPLETADO", nullable=False)
    summary = Column(String(500), nullable=True)
    details = Column(Text, nullable=True)

    brca1_path = Column(String(500), nullable=True)
    brca2_path = Column(String(500), nullable=True)

    patient = relationship("Patient", back_populates="analyses")
