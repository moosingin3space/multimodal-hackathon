import type { DailyReport, DiscoverResponse, Signal, SignalsResponse } from "./types";

const AGENT_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/run`
  : "http://localhost:8080/run";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_KEY = (import.meta.env.VITE_API_KEY as string) || "dev";

async function runAgent(prompt: string, retries = 4): Promise<string> {
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(AGENT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (res.status === 429 && attempt < retries) {
      const retryAfter = Number(res.headers.get("Retry-After") ?? 0);
      const delay = retryAfter > 0
        ? retryAfter * 1000
        : Math.min(1000 * 2 ** attempt + Math.random() * 500, 30_000);
      await new Promise((r) => setTimeout(r, delay));
      continue;
    }
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`${res.status}: ${text}`);
    }
    const data = await res.json() as { response?: string; output?: string };
    return data.response ?? data.output ?? JSON.stringify(data);
  }
}

function parseCompetitorList(text: string): string[] {
  // Try JSON array first
  const jsonMatch = text.match(/\[[\s\S]*?\]/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[0]) as unknown[];
      const names = parsed.filter((x): x is string => typeof x === "string");
      if (names.length > 0) return names;
    } catch { /* fall through */ }
  }
  // Fall back: extract lines that look like company names (numbered or bulleted)
  return text
    .split("\n")
    .map((l) => l.replace(/^[\s\d.\-*•]+/, "").trim())
    .filter((l) => l.length > 2 && l.length < 60 && !/^[a-z]/.test(l))
    .slice(0, 8);
}

// ---------------------------------------------------------------------------
// Discovery
// ---------------------------------------------------------------------------
export async function discoverCompetitors(company: string): Promise<DiscoverResponse> {
  const res = await fetch(
    `${API_BASE}/api/discover?company_name=${encodeURIComponent(company)}`,
    { method: "POST", headers: { Authorization: `Bearer ${API_KEY}` } },
  );
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<DiscoverResponse>;
}

export const getCompetitors = (company: string): Promise<{ company: string; competitors: string[] }> =>
  discoverCompetitors(company);

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------
export const getSignals = (
  company: string,
  options: { mode?: string; competitor?: string; limit?: number; competitors?: string[] } = {}
): Promise<SignalsResponse> => {
  const modeLabel = options.mode === "investor" ? "investor" : "employee";
  const competitorClause = options.competitor ? ` focused on ${options.competitor}` : "";
  const knownCompetitors = options.competitors ?? [];
  const competitorListClause = knownCompetitors.length
    ? ` Known competitors: ${knownCompetitors.join(", ")}. Each signal's "competitor" field must exactly match one of these names.`
    : "";
  return runAgent(
    `Return recent competitive intelligence signals for ${company}${competitorClause} from a ${modeLabel} perspective.${competitorListClause} ` +
    `Return JSON matching: {"signals": [{"id": "unique-id", "competitor": "ExactCompetitorName", "type": "product_launch|pricing_change|hiring_surge|partnership|exec_move|other", "summary": "...", "urgency": "low|medium|high|critical", "surface_now": false, "detected_at": "ISO8601", "source_url": null, "mode": "${modeLabel}"}]}`
  ).then((text) => {
    const m = text.match(/\{[\s\S]*\}/);
    let parsed: SignalsResponse = { company, count: 0, signals: [] };
    try { if (m) parsed = JSON.parse(m[0]) as SignalsResponse; } catch { /* */ }

    // Post-process: fill in missing/invalid fields so signals are always tagged correctly
    const signals = (parsed.signals ?? []).map((s, i) => {
      const competitor =
        knownCompetitors.find((c) => c.toLowerCase() === s.competitor?.toLowerCase()) ??
        s.competitor ??
        knownCompetitors[i % knownCompetitors.length] ??
        company;
      return {
        ...s,
        id: s.id || `${competitor}-${i}-${Date.now()}`,
        competitor,
        detected_at: s.detected_at || new Date().toISOString(),
        surface_now: s.surface_now ?? false,
        mode: s.mode || modeLabel,
      };
    });

    return { ...parsed, signals };
  });
};

export const getUrgentSignals = (company: string): Promise<SignalsResponse> =>
  getSignals(company, { mode: "employee" });

export const getCompetitorSignals = (name: string): Promise<SignalsResponse> =>
  getSignals(name);

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const getDailyReport = async (company: string): Promise<DailyReport> => {
  const res = await fetch(`${API_BASE}/api/report?company=${encodeURIComponent(company)}`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<DailyReport>;
};

export const getCompetitorReport = (name: string): Promise<CompetitorReport> =>
  runAgent(
    `Give a competitive intelligence report for ${name}. ` +
    `Return JSON: {"competitor","trajectory","momentum_score","threat_level","narrative","strategic_inference"}`
  ).then((text) => {
    const m = text.match(/\{[\s\S]*\}/);
    try { if (m) return JSON.parse(m[0]) as CompetitorReport; } catch { /* */ }
    return { competitor: name, trajectory: "unknown", momentum_score: 50, threat_level: "medium", narrative: text, strategic_inference: "" };
  });

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
export const triggerAgentRun = async (company: string): Promise<{ status: string }> => {
  const res = await fetch(
    `${API_BASE}/api/agent/run?company_name=${encodeURIComponent(company)}`,
    { method: "POST", headers: { Authorization: `Bearer ${API_KEY}` } },
  );
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<{ status: string }>;
};

// ---------------------------------------------------------------------------
// Chat (streaming — falls back to non-streaming via /run)
// ---------------------------------------------------------------------------
export async function* streamChat(
  prompt: string,
  company: string
): AsyncGenerator<string> {
  const text = await runAgent(`Context: competitive intelligence for ${company}. ${prompt}`);
  yield text;
}
