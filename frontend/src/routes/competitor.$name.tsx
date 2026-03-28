import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/competitor/$name")({
  component: CompetitorDeepDive,
});

function CompetitorDeepDive() {
  const { name } = Route.useParams();

  return (
    <div>
      <h1>{name}</h1>
      {/* TODO: signal history, trajectory chart, chat assistant */}
      <p>Deep dive coming soon.</p>
    </div>
  );
}
