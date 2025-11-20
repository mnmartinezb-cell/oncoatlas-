oncoatlas/
│
├─ backend/
│  │
│  ├─ app/
│  │  │
│  │  ├─ api/
│  │  │   ├─ __init__.py
│  │  │   ├─ analysis.py           # endpoint /analysis/run
│  │  │   ├─ patients.py           # (luego) CRUD pacientes
│  │  │   ├─ auth.py               # (luego) login/roles
│  │  │
│  │  ├─ services/
│  │  │   ├─ __init__.py
│  │  │   ├─ analysis_engine.py    # módulo de análisis genético ✅
│  │  │   ├─ pdf_generator.py      # (luego) generar PDF del reporte
│  │  │
│  │  ├─ __init__.py
│  │  ├─ main.py                   # arranque de la API FastAPI
│  │  ├─ database.py               # conexión a SQLite
│  │  ├─ models.py                 # modelos SQLAlchemy (users, patients, variants...)
│  │  ├─ schemas.py                # modelos Pydantic
│  │  ├─ crud.py                   # operaciones DB
│  │
│  ├─ requirements.txt             # dependencias backend
│  ├─ create_tables.py             # inicializa BD (Base.metadata.create_all)
│
├─ frontend/
│  ├─ public/
│  │   └─ index.html               # frontend mínimo de prueba
│  └─ src/                         # (si luego usas React)
│
├─ refs/
│  ├─ BRCA1_reference.fasta        # referencia oficial BRCA1 (la debes colocar aquí)
│  └─ BRCA2_reference.fasta        # referencia oficial BRCA2
│
├─ storage/
│  ├─ fastas/                      # aquí se guardan FASTA del paciente
│  │   └─ {patient_id}/            # se crea cuando subes archivos
│  │       ├─ archivo1.fasta
│  │       └─ archivo2.fasta
│  └─ reports/                     # JSON y PDF de análisis generados
│
├─ tests/
│  ├─ fasta_samples/               # muestras para pruebas del motor
│  │   ├─ brca1_demo.fasta
│  │   └─ brca2_demo.fasta
│  └─ test_analysis.py             # (luego) pruebas unitarias
│
└─ docs/
   └─ README.md                    # documentación del proyecto

# Oncoatlas empty structure
