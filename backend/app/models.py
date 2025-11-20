# app/models.py

from datetime import datetime, date

from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    document_id = Column(String, unique=True, index=True)  # cédula, etc.
    birth_date = Column(Date, nullable=True)
    sex = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship(
        "Analysis",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    overall_risk = Column(String, nullable=False)

    patient = relationship("Patient", back_populates="analyses")
    mutations = relationship(
        "Mutation",
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Mutation(Base):
    __tablename__ = "mutations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(
        Integer,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gene = Column(String, nullable=False)
    hgvs_c = Column(String, nullable=False)
    significance = Column(String, nullable=False)  # Pathogenic, VUS, etc.
    source = Column(String, nullable=True)  # ClinVar, demo, etc.

    analysis = relationship("Analysis", back_populates="mutations")
