import api from "./client";
import type { Patient } from "@/types/api";

export async function searchPatients(params?: {
  family?: string;
  given?: string;
  gender?: string;
  _count?: number;
}): Promise<Patient[]> {
  const { data } = await api.get("/fhir/Patient", { params });
  return data.entry ?? data;
}

export async function getPatient(id: number): Promise<Patient> {
  const { data } = await api.get(`/fhir/Patient/${id}`);
  return data;
}

export async function createPatient(
  patient: Partial<Patient>,
): Promise<Patient> {
  const { data } = await api.post("/fhir/Patient", patient);
  return data;
}

export async function updatePatient(
  id: number,
  patient: Partial<Patient>,
): Promise<Patient> {
  const { data } = await api.put(`/fhir/Patient/${id}`, patient);
  return data;
}
