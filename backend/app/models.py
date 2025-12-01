# backend/app/models.py

"""
Modelos de base de datos para Oncoatlas.

Define:
- Doctor: usuarios médicos (y/o administrador).
- Patient: pacientes sobre los que se hace el análisis genético.
- Analysis: resultados de análisis BRCA1/BRCA2 por paciente.
"""

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

    # Relación 1-N: un médico tiene muchos pacientes
    patients = relationship(
        "Patient",
        back_populates="doctor",
        cascade="all, delete-orphan",
    )


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(200), nullable=False)
    document_id = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    sex = Column(String(10), nullable=False)

    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    # Relación inversa al médico
    doctor = relationship("Doctor", back_populates="patients")

    # Relación 1-N: un paciente tiene muchos análisis
    analyses = relationship(
        "Analysis",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="COMPLETADO", nullable=False)

    # Resumen corto para mostrar en tablas / frontend
    summary = Column(String(500), nullable=True)

    # Detalles extensos del análisis (JSON serializado, texto, etc.)
    details = Column(Text, nullable=True)

    # Rutas a los archivos FASTA usados en este análisis (opcional)
    brca1_path = Column(String(500), nullable=True)
    brca2_path = Column(String(500), nullable=True)

    # Relación inversa al paciente
    patient = relationship("Patient", back_populates="analyses")
