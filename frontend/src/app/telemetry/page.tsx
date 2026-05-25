import { DashboardShell } from "@/components/layout/dashboard-shell";
import { TelemetryFeed } from "@/components/agent/telemetry-feed";

export default function TelemetryPage() {
  return (
    <DashboardShell>
      <TelemetryFeed />
    </DashboardShell>
  );
}