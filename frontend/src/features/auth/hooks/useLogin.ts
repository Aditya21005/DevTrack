import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { authService } from "../api/auth.service";
import { useAuthStore } from "../store/auth.store";
import type { LoginInput } from "../types";

export function useLogin() {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);

  return useMutation({
    mutationFn: (input: LoginInput) => authService.login(input),
    onSuccess: (session) => {
      setSession(session.user, session.accessToken);
      navigate("/app/dashboard", { replace: true });
    },
  });
}
