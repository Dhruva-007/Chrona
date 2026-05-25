import { DashboardShell } from "@/components/layout/dashboard-shell";

export default function InfrastructurePage() {
  return (
    <DashboardShell>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-900">
          Infrastructure Graph
        </h1>
      </div>
    </DashboardShell>
  );
}