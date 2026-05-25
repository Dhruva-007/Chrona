import { Badge } from "@/components/ui/badge";

export function IncidentBanner() {
  return (
    <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">
            Active Incident Detected
          </h2>
          <p className="text-sm text-slate-300 mt-1">
            PostgreSQL Primary failure triggering cascading outage.
          </p>
        </div>

        <Badge className="bg-amber-500/20 text-amber-200">
          Severity: SEV-1
        </Badge>
      </div>
    </div>
  );
}