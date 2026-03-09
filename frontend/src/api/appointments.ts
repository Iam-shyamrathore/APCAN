import api from "./client";
import type { Appointment } from "@/types/api";

export async function searchAppointments(params?: {
  patient?: number;
  status?: string;
  date?: string;
  date_ge?: string;
  date_le?: string;
  _count?: number;
}): Promise<Appointment[]> {
  const { data } = await api.get("/fhir/Appointment", { params });
  return data.entry ?? data;
}

export async function getAppointment(id: number): Promise<Appointment> {
  const { data } = await api.get(`/fhir/Appointment/${id}`);
  return data;
}

export async function createAppointment(
  appt: Partial<Appointment>,
): Promise<Appointment> {
  const { data } = await api.post("/fhir/Appointment", appt);
  return data;
}

export async function updateAppointment(
  id: number,
  appt: Partial<Appointment>,
): Promise<Appointment> {
  const { data } = await api.put(`/fhir/Appointment/${id}`, appt);
  return data;
}
