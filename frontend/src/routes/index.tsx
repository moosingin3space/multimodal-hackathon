import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { discoverCompetitors } from "../lib/api";

export const Route = createFileRoute("/")({
  component: Onboarding,
});

function Onboarding() {
  const [company, setCompany] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await discoverCompetitors(company);
    navigate({ to: "/dashboard", search: { company } });
  }

  return (
    <div>
      <h1>ScoutAgent</h1>
      <p>Enter your company name to start tracking competitors.</p>
      <form onSubmit={handleSubmit}>
        <input
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Acme Corp"
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Discovering…" : "Get started"}
        </button>
      </form>
    </div>
  );
}
