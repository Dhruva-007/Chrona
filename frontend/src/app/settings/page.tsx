import { DashboardShell } from "@/components/layout/dashboard-shell";

export default function SettingsPage() {
  return (
    <DashboardShell>
      <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-900">
          Settings
        </h1>

        <p className="mt-3 text-slate-500">
          Provider configuration and preferences.
        </p>
      </div>
    </DashboardShell>
  );
}