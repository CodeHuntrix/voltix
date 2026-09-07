import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

// Use LAN IP in Expo Go; default to localhost for simulators
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

async function storageGet(key: string): Promise<string | null> {
  if (Platform.OS === "web") {
    return localStorage.getItem(key);
  }
  return SecureStore.getItemAsync(key);
}

async function storageSet(key: string, value: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

async function storageDel(key: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export const authStore = {
  getToken: () => storageGet("access_token"),
  setToken: (t: string) => storageSet("access_token", t),
  getSiteId: () => storageGet("site_id"),
  setSiteId: (id: string) => storageSet("site_id", id),
  clear: async () => {
    await storageDel("access_token");
    await storageDel("site_id");
  },
};

async function request<T>(path: string, opts: RequestInit & { token?: string | null } = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;
  const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  orgs: (token: string) => request<any[]>("/api/v1/orgs", { token }),
  sites: (token: string, orgId: string) =>
    request<any[]>(`/api/v1/orgs/${orgId}/sites`, { token }),
  live: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/live`, { token }),
  rank: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/rank`, { token }),
  alerts: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/alerts`, { token }),
  autocutList: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/autocut`, { token }),
  autocutDecide: (token: string, id: string, approve: boolean) =>
    request(`/api/v1/autocut/${id}/decide`, {
      method: "POST",
      token,
      body: JSON.stringify({ approve }),
    }),
  mvReports: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/mv/reports`, { token }),
  pushToken: (token: string, push_token: string) =>
    request("/api/v1/auth/push-token", {
      method: "PUT",
      token,
      body: JSON.stringify({ push_token }),
    }),
};
