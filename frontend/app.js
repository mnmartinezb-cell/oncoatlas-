// frontend/app.js

// =======================================================
// Configuración
// =======================================================

// Ajusta esta URL si cambias el puerto del backend
const API_BASE = "http://127.0.0.1:8000";

// Helper rápido para obtener elementos
const $ = (id) => document.getElementById(id);

// Estado simple en memoria
let currentDoctor = null;
let currentPatient = null;

// =======================================================
// Utilidades de UI
// =======================================================

function setPanelVisible(element, visible) {
  if (!element) return;
  element.classList.remove("panel-hidden", "panel-visible");
  element.classList.add(visible ? "panel-visible" : "panel-hidden");
}

function showRoleSelection() {
  setPanelVisible($("role-selection"), true);
  setPanelVisible($("admin-section"), false);
  setPanelVisible($("doctor-section"), false);
  setPanelVisible($("doctor-dashboard"), false);
  setPanelVisible($("patient-detail-section"), false);
}

function showAdminPanel() {
  setPanelVisible($("role-selection"), false);
  setPanelVisible($("admin-section"), true);
  setPanelVisible($("doctor-section"), false);
  setPanelVisible($("doctor-dashboard"), false);
  setPanelVisible($("patient-detail-section"), false);
}

function showDoctorSelection() {
  setPanelVisible($("role-selection"), false);
  setPanelVisible($("admin-section"), false);
  setPanelVisible($("doctor-section"), true);
  setPanelVisible($("doctor-dashboard"), false);
  setPanelVisible($("patient-detail-section"), false);
}

function showDoctorDashboard() {
  setPanelVisible($("role-selection"), false);
  setPanelVisible($("admin-section"), false);
  setPanelVisible($("doctor-section"), false);
  setPanelVisible($("doctor-dashboard"), true);
  // el detalle de paciente se abre aparte
}

function showPatientDetailSection() {
  setPanelVisible($("patient-detail-section"), true);
}

// =======================================================
// Utilidades de red
// =======================================================

async function fetchJSON(url, options = {}) {
  const finalOptions = {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
  };

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !finalOptions.headers["Content-Type"]
  ) {
    finalOptions.headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, finalOptions);

  if (!response.ok) {
    let detail = "";
    try {
      const data = await response.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      detail = response.statusText;
    }
    throw new Error(`Error ${response.status}: ${detail}`);
  }

  // Algunas respuestas pueden no tener cuerpo (204)
  try {
    return await response.json();
  } catch {
    return null;
  }
}

// =======================================================
// DOCTORES
// =======================================================

async function loadDoctorsForAdmin() {
  const doctors = await fetchJSON(`${API_BASE}/admin/doctors`);
  const tbody = $("doctors-table-body");
  if (!tbody) return;

  tbody.innerHTML = "";
  doctors.forEach((doc) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${doc.id}</td>
      <td>${doc.name}</td>
      <td>${doc.email || ""}</td>
      <td>${doc.specialty || ""}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadDoctorsForSelection() {
  const doctors = await fetchJSON(`${API_BASE}/admin/doctors`);
  const select = $("doctor-select");
  if (!select) return;

  select.innerHTML = "";
  if (!doctors.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No hay médicos registrados";
    select.appendChild(opt);
    return;
  }

  doctors.forEach((doc) => {
    const opt = document.createElement("option");
    opt.value = String(doc.id);
    opt.textContent = `${doc.id} – ${doc.name}`;
    select.appendChild(opt);
  });
}

async function handleCreateDoctor(event) {
  event.preventDefault();

  const name = $("doctor-name").value.trim();
  const email = $("doctor-email").value.trim();
  const specialty = $("doctor-specialty").value.trim();

  if (!name || !email) {
    alert("Nombre y correo son obligatorios.");
    return;
  }

  const payload = {
    name,
    email,
    specialty,
  };

  try {
    await fetchJSON(`${API_BASE}/admin/doctors`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    alert("Médico creado correctamente.");
    $("admin-create-doctor-form").reset();
    await loadDoctorsForAdmin();
    await loadDoctorsForSelection();
  } catch (err) {
    console.error(err);
    alert("No se pudo crear el médico: " + err.message);
  }
}

// =======================================================
// PACIENTES
// =======================================================

async function loadPatientsForDoctor(doctorId) {
  const patients = await fetchJSON(
    `${API_BASE}/doctors/${doctorId}/patients`
  );
  const tbody = $("patients-table-body");
  if (!tbody) return;

  tbody.innerHTML = "";

  patients.forEach((p) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.full_name}</td>
      <td>${p.document_id}</td>
      <td><button class="secondary-btn" data-patient-id="${p.id}">Ver detalle</button></td>
    `;
    tbody.appendChild(tr);
  });

  // Eventos "Ver detalle"
  tbody.querySelectorAll("button[data-patient-id]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pid = parseInt(btn.getAttribute("data-patient-id"), 10);
      openPatientDetail(pid);
    });
  });
}

async function handleCreatePatient(event) {
  event.preventDefault();

  if (!currentDoctor) {
    alert("Primero selecciona un médico.");
    return;
  }

  const full_name = $("patient-full-name").value.trim();
  const document_id = $("patient-document").value.trim();
  const date_of_birth = $("patient-dob").value;
  const sex = $("patient-sex").value;

  if (!full_name || !document_id) {
    alert("Nombre y documento son obligatorios.");
    return;
  }

  const payload = {
    full_name,
    document_id,
    date_of_birth,
    sex,
  };

  try {
    await fetchJSON(
      `${API_BASE}/doctors/${currentDoctor.id}/patients`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
    alert("Paciente creado correctamente.");
    $("patient-form").reset();
    await loadPatientsForDoctor(currentDoctor.id);
  } catch (err) {
    console.error(err);
    alert("No se pudo crear el paciente: " + err.message);
  }
}

// =======================================================
// DETALLE DEL PACIENTE + ANÁLISIS
// =======================================================

async function openPatientDetail(patientId) {
  try {
    const patient = await fetchJSON(`${API_BASE}/patients/${patientId}`);
    currentPatient = patient;

    // Rellenar info básica
    const infoDiv = $("patient-detail-info");
    if (infoDiv) {
      infoDiv.innerHTML = `
        <p><strong>ID:</strong> ${patient.id}</p>
        <p><strong>Nombre:</strong> ${patient.full_name}</p>
        <p><strong>Documento:</strong> ${patient.document_id}</p>
        <p><strong>Fecha de nacimiento:</strong> ${
          patient.date_of_birth || ""
        }</p>
        <p><strong>Sexo:</strong> ${patient.sex || ""}</p>
      `;
    }

    // Guardar ID actual en input hidden
    const hiddenInput = $("current-patient-id");
    if (hiddenInput) {
      hiddenInput.value = String(patient.id);
    }

    showPatientDetailSection();
    await loadAnalysesForPatient(patient.id);
  } catch (err) {
    console.error(err);
    alert("No se pudo cargar el detalle del paciente: " + err.message);
  }
}

async function loadAnalysesForPatient(patientId) {
  const analyses = await fetchJSON(
    `${API_BASE}/patients/${patientId}/analyses`
  );
  const tbody = $("analyses-table-body");
  if (!tbody) return;

  tbody.innerHTML = "";

  analyses.forEach((an) => {
    const createdAt = an.created_at
      ? new Date(an.created_at).toLocaleString()
      : "";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${an.id}</td>
      <td>${createdAt}</td>
      <td>${an.summary || ""}</td>
      <td><a href="${API_BASE}/patients/${patientId}/analyses/${an.id}/report" target="_blank">Informe PDF</a></td>
    `;
    tbody.appendChild(tr);
  });
}

async function handleRunAnalysis(event) {
  event.preventDefault();

  const patientId = parseInt(
    $("current-patient-id").value || "0",
    10
  );
  if (!patientId) {
    alert("No hay paciente seleccionado.");
    return;
  }

  const brca1File = $("brca1-file").files[0];
  const brca2File = $("brca2-file").files[0];

  if (!brca1File || !brca2File) {
    alert("Por favor selecciona los archivos FASTA de BRCA1 y BRCA2.");
    return;
  }

  const formData = new FormData();
  formData.append("brca1_file", brca1File);
  formData.append("brca2_file", brca2File);

  try {
    await fetchJSON(
      `${API_BASE}/patients/${patientId}/analyses`,
      {
        method: "POST",
        body: formData,
      }
    );
    alert("Análisis ejecutado correctamente.");
    $("analysis-form").reset();
    await loadAnalysesForPatient(patientId);
  } catch (err) {
    console.error(err);
    alert("No se pudo ejecutar el análisis: " + err.message);
  }
}

// =======================================================
// Inicialización
// =======================================================

document.addEventListener("DOMContentLoaded", () => {
  console.log("Oncoatlas frontend cargado");

  // Navegación de roles
  $("btn-admin")?.addEventListener("click", async () => {
    showAdminPanel();
    try {
      await loadDoctorsForAdmin();
    } catch (err) {
      console.error(err);
      alert("No se pudieron cargar los médicos: " + err.message);
    }
  });

  $("btn-doctor")?.addEventListener("click", async () => {
    showDoctorSelection();
    try {
      await loadDoctorsForSelection();
    } catch (err) {
      console.error(err);
      alert("No se pudieron cargar los médicos: " + err.message);
    }
  });

  $("back-to-roles-from-admin")?.addEventListener("click", showRoleSelection);
  $("back-to-roles-from-doctor")?.addEventListener("click", showRoleSelection);

  // Entrar como médico
  $("enter-doctor-btn")?.addEventListener("click", async () => {
    const select = $("doctor-select");
    if (!select || !select.value) {
      alert("Selecciona un médico.");
      return;
    }
    const doctorId = parseInt(select.value, 10);
    const doctorName =
      select.options[select.selectedIndex]?.textContent || "";

    currentDoctor = { id: doctorId, name: doctorName };
    const infoDiv = $("doctor-info");
    if (infoDiv) {
      infoDiv.textContent = `Médico activo: ${doctorName}`;
    }

    showDoctorDashboard();
    try {
      await loadPatientsForDoctor(doctorId);
    } catch (err) {
      console.error(err);
      alert("No se pudieron cargar los pacientes: " + err.message);
    }
  });

  // Formularios
  $("admin-create-doctor-form")?.addEventListener(
    "submit",
    handleCreateDoctor
  );
  $("patient-form")?.addEventListener("submit", handleCreatePatient);
  $("analysis-form")?.addEventListener("submit", handleRunAnalysis);

  // Cerrar detalle de paciente
  $("close-patient-detail")?.addEventListener("click", () => {
    setPanelVisible($("patient-detail-section"), false);
  });

  // Estado inicial
  showRoleSelection();
});
