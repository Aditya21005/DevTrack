import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { AuthUser, LoginInput, LoginResponse } from "../types";

interface ApiAuthUser {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string | null;
  is_active: boolean;
  last_login_at?: string | null;
}

interface ApiLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: ApiAuthUser;
}

function mapApiUser(user: ApiAuthUser): AuthUser {
  return {
    id: user.id,
    name: user.display_name,
    email: user.email,
    role: "member",
  };
}

function mapApiLoginResponse(response: ApiLoginResponse): LoginResponse {
  return {
    accessToken: response.access_token,
    user: mapApiUser(response.user),
  };
}

export const authService = {
  async login(input: LoginInput): Promise<LoginResponse> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(450);
      return {
        accessToken: "mock-devtrack-session-token",
        user: {
          id: "usr_01",
          name: "Avery Chen",
          email: input.email,
          role: "owner",
        },
      };
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.post<ApiLoginResponse>("/auth/login", input);
    return mapApiLoginResponse(response.data);
  },
};

