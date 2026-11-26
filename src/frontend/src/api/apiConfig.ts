import { RestClient } from "./restClient";

export interface PublicApiEnv {
  VITE_API_BASE_URL?: string;
}

export function getApiBaseUrl(env: PublicApiEnv = import.meta.env as PublicApiEnv): string | null {
  const value = env.VITE_API_BASE_URL?.trim().replace(/\/+$/, "") ?? "";
  return value.length > 0 ? value : null;
}

export function createRestClient(env: PublicApiEnv = import.meta.env as PublicApiEnv): RestClient | null {
  const baseUrl = getApiBaseUrl(env);
  return baseUrl === null ? null : new RestClient({ baseUrl });
}
