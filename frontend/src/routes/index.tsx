import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { discoverCompetitors } from "../lib/api";

export const Route = createFileRoute("/")({
  component: Onboarding,
});

function Onboarding() {
  const [company, setCompany] = useState("");
  const [loading, setLoading] = useState(false);
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!company.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await discoverCompetitors(company.trim());
      setCompetitors(res.competitors);
      // Brief pause so user sees the competitor list before navigating
      await new Promise((r) => setTimeout(r, 1200));
      navigate({ to: "/dashboard", search: { company: company.trim(), competitors: res.competitors } });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Discovery failed");
      setLoading(false);
    }
  }

  return (
    <div className="onboarding">
      <div className="onboarding-logo">ScoutAgent</div>
      <p className="onboarding-sub">
        Autonomous competitive intelligence. Enter your company name — we'll
        discover your rivals and start watching them 24/7.
      </p>

      <form className="onboarding-form" onSubmit={handleSubmit}>
        <input
          className="onboarding-input"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="e.g. Cisco, Stripe, OpenAI…"
          required
          disabled={loading}
          autoFocus
        />
        <button className="onboarding-btn" type="submit" disabled={loading}>
          {loading ? (
            <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
              <span className="spinner" />
              {competitors.length > 0 ? "Loading dashboard…" : "Discovering competitors…"}
            </span>
          ) : (
            "Start watching →"
          )}
        </button>
        {error && (
          <p style={{ color: "var(--red)", fontSize: 13, marginTop: 10, textAlign: "center" }}>
            {error}
          </p>
        )}
      </form>

      {competitors.length > 0 && (
        <div className="competitors-preview">
          <div className="competitors-preview-label">Competitors discovered</div>
          <div className="competitors-chips">
            {competitors.map((c) => (
              <span key={c} className="chip">{c}</span>
            ))}
          </div>
        </div>
      )}

      <p style={{ marginTop: 48, fontSize: 12, color: "var(--text-muted)", textAlign: "center" }}>
        Powered by DigitalOcean Gradient · Gemini 2.0 Flash · Railtracks
      </p>
    </div>
  );
}
