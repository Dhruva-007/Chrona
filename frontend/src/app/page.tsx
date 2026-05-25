import { DashboardShell } from "@/components/layout/dashboard-shell";
import { IncidentBanner } from "@/components/dashboard/incident-banner";
import { HealthSummary } from "@/components/dashboard/health-summary";
import { SimulationSummary } from "@/components/dashboard/simulation-summary";
import { InfrastructureGraph } from "@/components/graph/infrastructure-graph";
import { IncidentAnalyst } from "@/components/ai/incident-analyst";
import { NarrativePanel } from "@/components/ai/narrative-panel";
import { TelemetryFeed } from "@/components/agent/telemetry-feed";
import { AIAgentConsole } from "@/components/agent/ai-agent-console";

import {
  fetchHealthSummary,
  fetchInfrastructureGraph,
  fetchRootCauseAnalysis,
  fetchSimulationSuite,
  fetchPostmortem,
  fetchTelemetry,
} from "@/lib/api";

export default async function Home() {
  const [
    healthResponse,
    analysis,
    suite,
    graph,
    postmortem,
    telemetry,
  ] = await Promise.all([
    fetchHealthSummary(),
    fetchRootCauseAnalysis(),
    fetchSimulationSuite(),
    fetchInfrastructureGraph(),
    fetchPostmortem(),
    fetchTelemetry(),
  ]);

  const health = healthResponse.data;
  const rootCause = analysis.data.primary_cause;

  const blastRadiusPercent =
    (analysis.data.blast_radius.length /
      health.total_nodes) *
    100;

  const recoveryConfidence =
    suite.data.simulations.replica_failover
      .confidence * 100;

  return (
    <DashboardShell>
      <div className="space-y-8">
        <IncidentBanner />

        <HealthSummary
          health={health}
          blastRadius={blastRadiusPercent}
          recoveryConfidence={recoveryConfidence}
        />

        <div className="grid gap-6 xl:grid-cols-2">
          <SimulationSummary suite={suite} />

          <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <h3 className="text-xl font-semibold text-slate-900">
              Root Cause Candidate
            </h3>

            <p className="mt-8 text-4xl font-semibold tracking-tight text-slate-900">
              {rootCause.node_name}
            </p>

            <p className="mt-4 text-base text-slate-500">
              Confidence:{" "}
              {Math.round(
                rootCause.confidence_score * 100
              )}
              %
            </p>

            <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-6 text-sm leading-7 text-slate-700">
              {rootCause.reasoning?.[0] ??
                "No reasoning available"}
            </div>
          </div>
        </div>

        <InfrastructureGraph
          graph={graph}
          suite={suite}
          telemetry={telemetry}
        />

        <div className="grid gap-6 lg:grid-cols-2">
          <TelemetryFeed />
          <AIAgentConsole />
        </div>

        <NarrativePanel
          postmortem={postmortem}
        />

        <IncidentAnalyst
          health={health}
          suite={suite}
        />
      </div>
    </DashboardShell>
  );
}