import { DashboardShell } from "@/components/layout/dashboard-shell";
import { AIAgentConsole } from "@/components/agent/ai-agent-console";

export default function AIAgentPage() {
  return (
    <DashboardShell>
      <AIAgentConsole />
    </DashboardShell>
  );
}