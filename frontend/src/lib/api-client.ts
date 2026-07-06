import axios from "axios";

import { authToken } from "./auth-token";
import { runtimeConfig } from "./runtime-config";

export const apiClient = axios.create({
  baseURL: runtimeConfig.apiBaseUrl,
  timeout: 15000,
});

apiClient.interceptors.request.use((config) => {
  const token = authToken.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      authToken.clear();
      window.dispatchEvent(new CustomEvent("devtrack:unauthorized"));
    }
    return Promise.reject(error);
  },
);


