import { GraphHealthSummary } from "@/lib/types";
import { StatusCard } from "./status-card";

interface Props {
  health: GraphHealthSummary["data"];
  blastRadius: number;
  recoveryConfidence: number;
}

export function HealthSummary({
  health,
  blastRadius,
  recoveryConfidence,
}: Props) {
  return (
    <div className="grid gap-6 xl:grid-cols-4 md:grid-cols-2">
      <StatusCard
        title="Infrastructure Health"
        value={`${Math.round(health.health_score)}%`}
        subtitle={`${health.degraded_nodes} degraded services`}
      />

      <StatusCard
        title="Critical Nodes"
        value={String(health.critical_nodes)}
        subtitle="Immediate investigation required"
      />

      <StatusCard
        title="Blast Radius"
        value={`${Math.round(blastRadius)}%`}
        subtitle="Potential cascading impact"
      />

      <StatusCard
        title="Recovery Confidence"
        value={`${Math.round(recoveryConfidence)}%`}
        subtitle="Replica failover success likelihood"
      />
    </div>
  );
}