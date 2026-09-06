const API_BASE = import.meta.env.VITE_API_URL ?? "";

export type TokenPair = { access_token: string; refresh_token: string };

async function request<T>(
  path: string,
  opts: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.headers.get("content-type")?.includes("text/csv")) {
    return (await res.text()) as T;
  }
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<TokenPair>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: (token: string) => request<any>("/api/v1/auth/me", { token }),
  orgs: (token: string) => request<any[]>("/api/v1/orgs", { token }),
  sites: (token: string, orgId: string) =>
    request<any[]>(`/api/v1/orgs/${orgId}/sites`, { token }),
  live: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/live`, { token }),
  rank: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/rank`, { token }),
  alerts: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/alerts`, { token }),
  ackAlert: (token: string, id: string) =>
    request(`/api/v1/alerts/${id}/ack`, { method: "POST", token }),
  machines: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/machines`, { token }),
  telemetry: (token: string, machineId: string) =>
    request<any[]>(`/api/v1/machines/${machineId}/telemetry?limit=120`, { token }),
  states: (token: string, machineId: string) =>
    request<any[]>(`/api/v1/machines/${machineId}/states`, { token }),
  autocutList: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/autocut`, { token }),
  autocutCreate: (token: string, machineId: string, reason: string) =>
    request("/api/v1/autocut", {
      method: "POST",
      token,
      body: JSON.stringify({ machine_id: machineId, reason }),
    }),
  autocutDecide: (token: string, id: string, approve: boolean) =>
    request(`/api/v1/autocut/${id}/decide`, {
      method: "POST",
      token,
      body: JSON.stringify({ approve }),
    }),
  mvBaselines: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/mv/baselines`, { token }),
  mvReports: (token: string, siteId: string) =>
    request<any[]>(`/api/v1/sites/${siteId}/mv/reports`, { token }),
  mvReportCreate: (token: string, siteId: string, body: object) =>
    request(`/api/v1/sites/${siteId}/mv/reports`, {
      method: "POST",
      token,
      body: JSON.stringify(body),
    }),
  mvExport: (token: string, siteId: string) =>
    request<string>(`/api/v1/sites/${siteId}/mv/export.csv`, { token }),
};

export function stateColor(state: string): string {
  switch (state) {
    case "ACTIVE":
      return "bg-state-active";
    case "IDLE":
      return "bg-state-idle";
    case "WASTE":
      return "bg-state-waste";
    default:
      return "bg-state-off";
  }
}
