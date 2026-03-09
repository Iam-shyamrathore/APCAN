import api from "./client";
import type { AuditLog } from "@/types/api";

export async function getAuditLogs(params?: {
  patient_id?: number;
  user_id?: number;
  session_id?: string;
  action?: string;
  limit?: number;
}): Promise<{ total: number; logs: AuditLog[] }> {
  const { data } = await api.get("/audit/logs", { params });
  return data;
}
