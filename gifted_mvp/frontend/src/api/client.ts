import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { currentLanguage } from "../i18n";
import { tokenStore } from "./tokens";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8001/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // The backend localizes server-driven content and AI output from this header.
  config.headers["Accept-Language"] = currentLanguage();
  return config;
});

// Transparent access-token refresh on a single 401, then retry once.
let refreshing: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh });
    // Refresh tokens rotate: the backend returns a new one and blacklists the old one.
    if (data.refresh) tokenStore.set({ access: data.access, refresh: data.refresh });
    else tokenStore.setAccess(data.access);
    return data.access;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      refreshing = refreshing ?? refreshAccess();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  },
);
