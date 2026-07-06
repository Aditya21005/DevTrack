import { create } from "zustand";

import { authToken } from "@/lib/auth-token";
import type { AuthUser } from "../types";

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  setSession: (user: AuthUser, token: string) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: authToken.get(),
  setSession: (user, token) => {
    authToken.set(token);
    set({ user, token });
  },
  clearSession: () => {
    authToken.clear();
    set({ user: null, token: null });
  },
}));
