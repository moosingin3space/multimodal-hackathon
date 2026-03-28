import { createFileRoute, Link } from "@tanstack/react-router";
import { z } from "zod";

const searchSchema = z.object({ company: z.string() });

export const Route = createFileRoute("/dashboard")({
  validateSearch: searchSchema,
  component: Dashboard,
});

function Dashboard() {
  const { company } = Route.useSearch();

  return (
    <div>
      <h1>Dashboard — {company}</h1>
      {/* TODO: live signal feed + daily report */}
      <p>Live feed coming soon.</p>
    </div>
  );
}
