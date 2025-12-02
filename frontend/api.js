const API_BASE_URL = "http://127.0.0.1:8000";

export async function runAnalysisForPatient(patientId, brca1File, brca2File) {
  const formData = new FormData();
  formData.append("patient_id", patientId);
  formData.append("brca1_file", brca1File);
  formData.append("brca2_file", brca2File);

  const response = await fetch(`${API_BASE_URL}/analysis/run_for_patient`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Error ${response.status}: ${errorText}`);
  }

  return await response.json();
}

