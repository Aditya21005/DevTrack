const explicitMockFlag = import.meta.env.VITE_USE_MOCK_API;

export const runtimeConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "/api",
  useMockApi: explicitMockFlag === "true" || (import.meta.env.DEV && explicitMockFlag !== "false"),
};
