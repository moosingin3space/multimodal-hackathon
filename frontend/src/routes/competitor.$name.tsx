import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { z } from "zod";
import { getCompetitorReport, getCompetitorSignals } from "../lib/api";
import type { CompetitorReport } from "../lib/api";
import type { Signal } from "../lib/types";

const searchSchema = z.object({ company: z.string().optional() });

export const Route = createFileRoute("/competitor/$name")({
  validateSearch: searchSchema,
  component: CompetitorDeepDive,
});

function CompetitorDeepDive() {
  const { name: encodedName } = Route.useParams();
  const { company } = Route.useSearch();
  const name = decodeURIComponent(encodedName);

  const [signals, setSignals] = useState<Signal[]>([]);
  const [report, setReport] = useState<CompetitorReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeMode, setActiveMode] = useState<"all" | "employee" | "investor">("all");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getCompetitorSignals(name),
      getCompetitorReport(name),
    ])
      .then(([sigRes, rep]) => {
        setSignals(sigRes.signals);
        setReport(rep);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [name]);

  const filtered =
    activeMode === "all"
      ? signals
      : signals.filter((s) => s.mode === activeMode || s.mode === "both");

  const momentumColor =
    (report?.momentum_score ?? 50) >= 70
      ? "var(--green)"
      : (report?.momentum_score ?? 50) >= 40
      ? "var(--yellow)"
      : "var(--red)";

  return (
    <div style={{ height: "100vh", overflow: "auto", background: "var(--bg)" }}>
      {/* Header */}
      <div className="deepdive-header" style={{ background: "var(--bg-card)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, paddingBottom: 16 }}>
          {company && (
            <Link
              to="/dashboard"
              search={{ company }}
              style={{ fontSize: 13, color: "var(--text-muted)" }}
            >
              ← {company}
            </Link>
          )}
        </div>
        <div className="deepdive-name">{name}</div>
        {report && (
          <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "12px 0" }}>
            <span className={`trajectory-value trajectory-${report.trajectory}`} style={{ padding: "4px 12px", borderRadius: 6, fontSize: 13 }}>
              {_trajectoryIcon(report.trajectory)} {report.trajectory}
            </span>
            <span className={`threat-badge urgency-${report.threat_level}`} style={{ padding: "4px 12px", borderRadius: 6, fontSize: 13 }}>
              {report.threat_level} threat
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Momentum</span>
              <div style={{ width: 100, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${report.momentum_score}%`, height: "100%", background: momentumColor, borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 13, fontWeight: 700, color: momentumColor }}>{report.momentum_score}</span>
            </div>
          </div>
        )}
      </div>

      <div className="deepdive-body">
        {/* Strategic summary */}
        {report && (
          <div className="trajectory-summary">
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.5px" }}>30-day analysis</div>
            <p style={{ margin: "0 0 10px", fontSize: 14, lineHeight: 1.6 }}>{report.narrative}</p>
            {report.strategic_inference && (
              <div style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: 8, padding: "10px 14px" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>Strategic inference</div>
                <div style={{ fontSize: 13, fontStyle: "italic", color: "var(--text-dim)" }}>{report.strategic_inference}</div>
              </div>
            )}
          </div>
        )}

        {/* Mode filter */}
        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          {(["all", "employee", "investor"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setActiveMode(m)}
              style={{
                padding: "6px 16px",
                borderRadius: 20,
                border: `1px solid ${activeMode === m ? "var(--accent)" : "var(--border)"}`,
                background: activeMode === m ? "rgba(59,130,246,0.12)" : "transparent",
                color: activeMode === m ? "var(--accent)" : "var(--text-muted)",
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)} {m === "all" ? `(${signals.length})` : `(${signals.filter(s => s.mode === m || s.mode === "both").length})`}
            </button>
          ))}
        </div>

        {/* Signal list */}
        {loading && (
          <div style={{ color: "var(--text-muted)", display: "flex", gap: 10 }}>
            <span className="spinner" /> Loading signals…
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filtered.map((signal, i) => (
            <DeepDiveSignalCard key={signal.id || i} signal={signal} />
          ))}
        </div>

        {!loading && filtered.length === 0 && (
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
            No signals in this category yet.
          </div>
        )}
      </div>
    </div>
  );
}

function DeepDiveSignalCard({ signal }: { signal: Signal }) {
  return (
    <div
      className={`signal-card urgency-${signal.urgency}${signal.surface_now ? " surface-now" : ""}`}
    >
      <div className="signal-header">
        <span className="signal-type">{signal.type.replace(/_/g, " ")}</span>
        <span
          style={{
            fontSize: 11,
            padding: "2px 8px",
            borderRadius: 4,
            background: signal.mode === "investor" ? "rgba(139,92,246,0.12)" : "rgba(59,130,246,0.12)",
            color: signal.mode === "investor" ? "var(--purple)" : "var(--accent)",
          }}
        >
          {signal.mode}
        </span>
        <span className="signal-time" style={{ marginLeft: "auto" }}>{_relativeTime(signal.detected_at)}</span>
      </div>

      <p className="signal-summary">{signal.summary}</p>

      {signal.gemini_analysis && (
        <div className="gemini-box">
          <div className="gemini-box-label">✦ Gemini image analysis</div>
          <div className="gemini-box-text">{signal.gemini_analysis}</div>
        </div>
      )}

      {signal.evidence && (
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8, fontStyle: "italic" }}>
          Evidence: {signal.evidence}
        </div>
      )}

      <div className="signal-footer" style={{ marginTop: 10 }}>
        <span className={`urgency-badge urgency-${signal.urgency}`}>{signal.urgency}</span>
        {signal.surface_now && <span className="now-badge">URGENT NOW</span>}
        {signal.momentum_delta !== undefined && signal.momentum_delta !== 0 && (
          <span style={{
            fontSize: 11,
            color: signal.momentum_delta > 0 ? "var(--green)" : "var(--red)",
            fontWeight: 700,
          }}>
            {signal.momentum_delta > 0 ? `+${signal.momentum_delta}` : signal.momentum_delta} momentum
          </span>
        )}
        {signal.source_url && (
          <a href={signal.source_url} target="_blank" rel="noopener noreferrer" className="source-link">
            Source ↗
          </a>
        )}
      </div>
    </div>
  );
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
