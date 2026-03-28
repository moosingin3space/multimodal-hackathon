import { createFileRoute, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { z } from "zod";
import {
  getDailyReport,
  getSignals,
  streamChat,
  triggerAgentRun,
} from "../lib/api";
import type { CompetitorSummary, DailyReport, Signal } from "../lib/types";

const searchSchema = z.object({ company: z.string(), competitors: z.array(z.string()).optional() });

export const Route = createFileRoute("/dashboard")({
  validateSearch: searchSchema,
  component: Dashboard,
});

type Mode = "employee" | "investor";
type PanelTab = "report" | "chat";

function Dashboard() {
  const { company, competitors: discoveredCompetitors } = Route.useSearch();
  const [mode, setMode] = useState<Mode>("employee");
  const [signals, setSignals] = useState<Signal[]>([]);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCompetitor, setActiveCompetitor] = useState<string | null>(null);
  const [panelTab, setPanelTab] = useState<PanelTab>("report");
  const [refreshing, setRefreshing] = useState(false);

  // Clear accumulated signals whenever the company or mode changes so we don't
  // mix signals from different contexts.
  useEffect(() => {
    setSignals([]);
  }, [company, mode]);

  const fetchSignals = useCallback(async () => {
    try {
      const res = await getSignals(company, { mode, limit: 100, competitors: discoveredCompetitors });
      setSignals(prev => {
        // Merge: existing signals win on conflict so already-visible signals don't flicker.
        const merged = new Map(res.signals.map(s => [s.id, s]));
        for (const s of prev) merged.set(s.id, s);
        return [...merged.values()]
          .sort((a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime())
          .slice(0, 25);
      });
    } catch (e) {
      console.error("fetchSignals:", e);
    }
  }, [company, mode, discoveredCompetitors]);

  const fetchReport = useCallback(async () => {
    try {
      const r = await getDailyReport(company);
      setReport(r);
    } catch (e) {
      console.error("fetchReport:", e);
    }
  }, [company]);

  useEffect(() => {
    setLoading(true);
    setRefreshing(true);
    // Kick off a fresh sweep immediately on load so the user never has to
    // manually trigger the first scan.
    triggerAgentRun(company).catch(console.error).finally(() => setRefreshing(false));
    Promise.all([fetchSignals(), fetchReport()]).finally(() => setLoading(false));
  }, [fetchSignals, fetchReport, company]);

  // Poll for new signals every 30s
  useEffect(() => {
    const id = setInterval(fetchSignals, 30_000);
    return () => clearInterval(id);
  }, [fetchSignals]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await triggerAgentRun(company);
      await Promise.all([fetchSignals(), fetchReport()]);
    } finally {
      setRefreshing(false);
    }
  }

  // Competitor list from report or derived from signals
  const competitors = report?.competitors ?? [];
  const competitorNames: string[] = (competitors.length > 0
    ? competitors.map((c) => c.name)
    : signals.some((s) => s.competitor)
    ? [...new Set(signals.map((s) => s.competitor))]
    : discoveredCompetitors ?? []
  ).filter(Boolean) as string[];

  const visibleSignals = activeCompetitor
    ? signals.filter((s) => s.competitor === activeCompetitor)
    : signals;

  const urgentCount = signals.filter((s) => s.surface_now).length;

  return (
    <div className="app-shell">
      {/* Top bar */}
      <header className="topbar">
        <Link to="/" style={{ textDecoration: "none", color: "inherit" }}>
          <span className="topbar-brand">ScoutAgent</span>
        </Link>
        <span className="topbar-company">watching {company}</span>
        {urgentCount > 0 && (
          <span className="now-badge">{urgentCount} urgent</span>
        )}
        <div className="topbar-right">
          <div className="mode-toggle">
            <button
              className={`mode-btn${mode === "employee" ? " active" : ""}`}
              onClick={() => setMode("employee")}
            >
              Employee
            </button>
            <button
              className={`mode-btn${mode === "investor" ? " active" : ""}`}
              onClick={() => setMode("investor")}
            >
              Investor
            </button>
          </div>
          <button
            className="sweep-btn"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? "Sweeping…" : "↻ Sweep now"}
          </button>
        </div>
      </header>

      <div className="main-layout">
        {/* Left sidebar — competitor list */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <div className="sidebar-label">Competitors</div>
            <div
              className={`competitor-item${activeCompetitor === null ? " active" : ""}`}
              onClick={() => setActiveCompetitor(null)}
            >
              <span className="competitor-dot" style={{ background: "var(--accent)" }} />
              <span className="competitor-name">All</span>
              <span className="competitor-count">{signals.length}</span>
            </div>
            {competitorNames.map((name, i) => {
              const count = signals.filter((s) => s.competitor === name).length;
              const summary = competitors.find((c) => c.name === name);
              const color = _threatColor(summary?.threat_level);
              return (
                <div
                  key={name}
                  className={`competitor-item${activeCompetitor === name ? " active" : ""}`}
                  onClick={() => setActiveCompetitor(name)}
                >
                  <span className="competitor-dot" style={{ background: color }} />
                  <span className="competitor-name">{name}</span>
                  <span className="competitor-count">{count}</span>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Main feed */}
        <main className="feed">
          <div className="feed-header">
            <span className="feed-title">
              {activeCompetitor ?? "All signals"}
            </span>
            <span className="feed-count">{visibleSignals.length} of 25 signals</span>
            {activeCompetitor && (
              <Link
                to="/competitor/$name"
                params={{ name: encodeURIComponent(activeCompetitor) }}
                style={{ fontSize: 12, marginLeft: "auto", color: "var(--accent)" }}
              >
                Deep dive →
              </Link>
            )}
          </div>

          {(loading || refreshing) && visibleSignals.length === 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--text-muted)" }}>
              <span className="spinner" /> Sweeping for signals…
            </div>
          )}

          {!loading && !refreshing && visibleSignals.length === 0 && (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
              No signals found. Try another sweep.
            </div>
          )}

          {visibleSignals.map((signal, i) => (
            <SignalCard key={signal.id || i} signal={signal} />
          ))}
        </main>

        {/* Right panel — report + chat */}
        <aside className="right-panel">
          <div className="panel-tabs">
            <button
              className={`panel-tab${panelTab === "report" ? " active" : ""}`}
              onClick={() => setPanelTab("report")}
            >
              Daily Report
            </button>
            <button
              className={`panel-tab${panelTab === "chat" ? " active" : ""}`}
              onClick={() => setPanelTab("chat")}
            >
              Ask Agent
            </button>
          </div>

          {panelTab === "report" ? (
            <ReportPanel report={report} loading={loading} />
          ) : (
            <ChatPanel company={company} />
          )}
        </aside>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Signal card
// ---------------------------------------------------------------------------

function SignalCard({ signal }: { signal: Signal }) {
  return (
    <div
      className={`signal-card urgency-${signal.urgency}${signal.surface_now ? " surface-now" : ""}`}
    >
      <div className="signal-header">
        <span className="signal-competitor">{signal.competitor}</span>
        <span className="signal-type">{_typeLabel(signal.type)}</span>
        <span className="signal-time">{_relativeTime(signal.detected_at)}</span>
      </div>

      <p className="signal-summary">{signal.summary}</p>

      {signal.gemini_analysis && (
        <div className="gemini-box">
          <div className="gemini-box-label">Gemini analysis</div>
          <div className="gemini-box-text">{signal.gemini_analysis}</div>
        </div>
      )}

      <div className="signal-footer">
        <span className={`urgency-badge urgency-${signal.urgency}`}>
          {signal.urgency}
        </span>
        {signal.surface_now && <span className="now-badge">URGENT</span>}
        {signal.gemini_analysis && <span className="gemini-tag">✦ Gemini</span>}
        {signal.source_url && (
          <a
            href={signal.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-link"
          >
            Source ↗
          </a>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Report panel
// ---------------------------------------------------------------------------

function ReportPanel({
  report,
  loading,
}: {
  report: DailyReport | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="panel-body" style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--text-muted)" }}>
        <span className="spinner" /> Building report…
      </div>
    );
  }
  if (!report || report.competitors.length === 0) {
    return (
      <div className="panel-body" style={{ color: "var(--text-muted)", fontSize: 13 }}>
        No report data yet. Run a sweep to generate intelligence.
      </div>
    );
  }

  return (
    <div className="panel-body">
      <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 14 }}>
        {report.date} · {report.total_signals_24h} signals in 24h
      </div>
      {report.competitors.map((c) => (
        <CompetitorReportCard key={c.name} summary={c} />
      ))}
    </div>
  );
}

function CompetitorReportCard({ summary }: { summary: CompetitorSummary }) {
  const momentumColor =
    summary.momentum_score >= 70
      ? "var(--green)"
      : summary.momentum_score >= 40
      ? "var(--yellow)"
      : "var(--red)";

  return (
    <div className="report-competitor">
      <div className="report-name">
        <Link
          to="/competitor/$name"
          params={{ name: encodeURIComponent(summary.name) }}
          style={{ color: "var(--text)" }}
        >
          {summary.name}
        </Link>
      </div>

      <div className="trajectory-row">
        <span className="trajectory-label">Trajectory</span>
        <span className={`trajectory-value trajectory-${summary.trajectory}`}>
          {_trajectoryIcon(summary.trajectory)} {summary.trajectory}
        </span>
        <span
          className={`threat-badge urgency-${summary.threat_level}`}
          style={{ marginLeft: "auto" }}
        >
          {summary.threat_level}
        </span>
      </div>

      <div className="momentum-bar">
        <span style={{ fontSize: 11, color: "var(--text-muted)", minWidth: 72 }}>
          Momentum
        </span>
        <div className="momentum-track">
          <div
            className="momentum-fill"
            style={{
              width: `${summary.momentum_score}%`,
              background: momentumColor,
            }}
          />
        </div>
        <span className="momentum-value">{summary.momentum_score}</span>
      </div>

      {summary.strategic_inference && (
        <p className="inference-text">"{summary.strategic_inference}"</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chat panel
// ---------------------------------------------------------------------------

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED = [
  "Should I be worried about Palo Alto?",
  "Which competitor is moving fastest?",
  "What's Juniper's trajectory?",
  "Any pricing threats this week?",
];

function ChatPanel({ company }: { company: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: `I'm monitoring competitors of ${company}. Ask me anything — hiring trends, product launches, threat analysis, momentum scores.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(prompt: string) {
    if (!prompt.trim() || streaming) return;
    const userMsg: ChatMessage = { role: "user", content: prompt };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    // Add placeholder for assistant response
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      let accumulated = "";
      for await (const chunk of streamChat(prompt, company)) {
        accumulated += chunk;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: accumulated };
          return updated;
        });
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Sorry, inference is unavailable. Check GRADIENT_MODEL_ACCESS_KEY.",
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <>
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.content || (msg.role === "assistant" && streaming ? (
              <span className="spinner" style={{ width: 14, height: 14 }} />
            ) : null)}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div style={{ padding: "0 16px 8px", display: "flex", flexWrap: "wrap", gap: 6 }}>
          {SUGGESTED.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              style={{
                background: "var(--bg-hover)",
                border: "1px solid var(--border)",
                borderRadius: 20,
                color: "var(--text-dim)",
                padding: "4px 12px",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder="Ask about any competitor…"
          rows={2}
          disabled={streaming}
        />
        <button className="chat-send" type="submit" disabled={streaming || !input.trim()}>
          {streaming ? "…" : "Send"}
        </button>
      </form>
    </>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function _threatColor(level?: string): string {
  switch (level) {
    case "critical": return "var(--critical)";
    case "high": return "var(--high)";
    case "medium": return "var(--medium)";
    default: return "var(--low)";
  }
}

function _typeLabel(type: string): string {
  return type.replace(/_/g, " ");
}

function _trajectoryIcon(t: string): string {
  switch (t) {
    case "accelerating": return "↑";
    case "declining": return "↓";
    default: return "→";
  }
}

function _relativeTime(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const h = Math.floor(diff / 3_600_000);
    if (h < 1) return "< 1h ago";
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  } catch {
    return "";
  }
}
