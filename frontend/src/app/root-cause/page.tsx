import { DashboardShell } from "@/components/layout/dashboard-shell";

export default function RootCausePage() {
  return (
    <DashboardShell>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-900">
          Root Cause Analysis
        </h1>
      </div>
    </DashboardShell>
  );
}