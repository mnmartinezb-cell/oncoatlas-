from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    document_number = Column(String(50), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    doctor_id = Column(Integer, nullable=True)

    # Relación con los análisis germinales
    germline_analyses = relationship("GermlineAnalysis", back_populates="patient")


class GermlineAnalysis(Base):
    __tablename__ = "germline_analyses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True, nullable=False)

    # Resumen corto para mostrar en tablas / histórico
    summary = Column(Text, nullable=True)

    # JSON completo del resultado del análisis, guardado como texto
    raw_result = Column(Text, nullable=False)

    # Fecha de creación del registro
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación inversa
    patient = relationship("Patient", back_populates="germline_analyses")


