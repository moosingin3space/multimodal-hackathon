const BASE = "/api";
const KEY = import.meta.env.VITE_API_KEY as string;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${KEY}`,
      ...init?.headers,
    },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const discoverCompetitors = (company: string) =>
  request<{ competitors: string[] }>(
    `/discover?company_name=${encodeURIComponent(company)}`,
    { method: "POST" }
  );

export const triggerAgentRun = (company: string) =>
  request<{ status: string }>(`/agent/run?company_name=${encodeURIComponent(company)}`, {
    method: "POST",
  });
