import type { DailyReport, DiscoverResponse, Signal, SignalsResponse } from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : "/api";
const KEY = (import.meta.env.VITE_API_KEY as string) || "dev";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${KEY}`,
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Discovery
// ---------------------------------------------------------------------------
export const discoverCompetitors = (company: string): Promise<DiscoverResponse> =>
  request<DiscoverResponse>(
    `/discover?company_name=${encodeURIComponent(company)}`,
    { method: "POST" }
  );

export const getCompetitors = (company: string): Promise<{ company: string; competitors: string[] }> =>
  request(`/competitors?company=${encodeURIComponent(company)}`);

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------
export const getSignals = (
  company: string,
  options: { mode?: string; competitor?: string; limit?: number } = {}
): Promise<SignalsResponse> => {
  const params = new URLSearchParams({ company });
  if (options.mode) params.set("mode", options.mode);
  if (options.competitor) params.set("competitor", options.competitor);
  if (options.limit) params.set("limit", String(options.limit));
  return request<SignalsResponse>(`/signals?${params}`);
};

export const getUrgentSignals = (company: string): Promise<SignalsResponse> =>
  request(`/signals/urgent?company=${encodeURIComponent(company)}`);

export const getCompetitorSignals = (name: string): Promise<SignalsResponse> =>
  request(`/signals/competitor/${encodeURIComponent(name)}`);

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const getDailyReport = (company: string): Promise<DailyReport> =>
  request(`/report?company=${encodeURIComponent(company)}`);

export const getCompetitorReport = (name: string): Promise<CompetitorReport> =>
  request(`/report/competitor/${encodeURIComponent(name)}`);

export interface CompetitorReport {
  competitor: string;
  trajectory: string;
  momentum_score: number;
  threat_level: string;
  narrative: string;
  strategic_inference: string;
}

// ---------------------------------------------------------------------------
// Agent
// ---------------------------------------------------------------------------
export const triggerAgentRun = (company: string): Promise<{ status: string }> =>
  request(`/agent/run?company_name=${encodeURIComponent(company)}`, { method: "POST" });

// ---------------------------------------------------------------------------
// Chat (streaming)
// ---------------------------------------------------------------------------
export async function* streamChat(
  prompt: string,
  company: string
): AsyncGenerator<string> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${KEY}`,
    },
    body: JSON.stringify({ prompt, company }),
  });

  if (!res.ok || !res.body) throw new Error(`Chat error: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    // SSE lines: "data: <content>"
    for (const line of chunk.split("\n")) {
      if (line.startsWith("data: ")) {
        yield line.slice(6);
      }
    }
  }
}
