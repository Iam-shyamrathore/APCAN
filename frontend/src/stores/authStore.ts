import { create } from "zustand";
import type { User } from "@/types/api";
import * as authApi from "@/api/auth";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;

  setTokens: (access: string, refresh: string) => void;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  fetchUser: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: false,
  error: null,

  setTokens: (access, refresh) =>
    set({ accessToken: access, refreshToken: refresh }),

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await authApi.login(email, password);
      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });
      await get().fetchUser();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Login failed";
      set({ error: msg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  signup: async (email, password, fullName) => {
    set({ isLoading: true, error: null });
    try {
      await authApi.signup(email, password, fullName);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Signup failed";
      set({ error: msg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  fetchUser: async () => {
    try {
      const user = await authApi.getMe();
      set({ user });
    } catch {
      set({ user: null, accessToken: null, refreshToken: null });
    }
  },

  logout: () =>
    set({ user: null, accessToken: null, refreshToken: null, error: null }),
}));
