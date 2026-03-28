import type { DailyReport, DiscoverResponse, Signal, SignalsResponse } from "./types";

const AGENT_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/run`
  : "http://localhost:8080/run";
// KEY kept for future Unkey integration
const _KEY = (import.meta.env.VITE_API_KEY as string) || "dev";
void _KEY;

async function runAgent(prompt: string): Promise<string> {
  const res = await fetch(AGENT_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  const data = await res.json() as { response?: string; output?: string };
  return data.response ?? data.output ?? JSON.stringify(data);
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
  const prompt =
    `List the top 5 direct competitors for ${company}. ` +
    `Return ONLY a JSON array of company name strings, no explanation. ` +
    `Example format: ["Company A", "Company B", "Company C"]`;
  const text = await runAgent(prompt);
  return { company, competitors: parseCompetitorList(text), cached: false };
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
export const getDailyReport = (company: string): Promise<DailyReport> =>
  runAgent(
    `Generate a daily competitive intelligence report for ${company}. ` +
    `Return JSON matching the DailyReport schema with fields: generated_at, target_company, report_date, competitor_summaries, executive_summary, urgent_watch, total_signals_processed.`
  ).then((text) => {
    const m = text.match(/\{[\s\S]*\}/);
    try { if (m) return JSON.parse(m[0]) as DailyReport; } catch { /* */ }
    return { company, date: new Date().toDateString(), generated_at: new Date().toISOString(), competitors: [], total_signals_24h: 0 };
  });

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
export const triggerAgentRun = (company: string): Promise<{ status: string }> =>
  runAgent(`Run a full competitive intelligence sweep for ${company}.`)
    .then(() => ({ status: "ok" }));

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
