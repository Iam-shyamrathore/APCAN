import api from "./client";
import type { User, TokenResponse } from "@/types/api";

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const { data } = await api.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function signup(
  email: string,
  password: string,
  fullName: string,
): Promise<User> {
  const { data } = await api.post<User>("/auth/signup", {
    email,
    password,
    full_name: fullName,
  });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}
