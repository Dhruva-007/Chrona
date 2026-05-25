import { Card } from "@/components/ui/card";
import { SimulationSuite } from "@/lib/types";

interface Props {
  suite: SimulationSuite;
}

export function SimulationSummary({ suite }: Props) {
  const sims = suite.data.simulations;

  const items = [
    sims.node_removal,
    sims.node_hardening,
    sims.replica_failover,
  ];

  return (
    <Card className="rounded-2xl border border-white/5 bg-slate-900/70 p-6">
      <h3 className="text-xl font-semibold tracking-tight mb-6">
        Counterfactual Simulations
      </h3>

      <div className="space-y-4">
        {items.map((sim) => (
          <div
            key={sim.type}
            className="rounded-xl border border-white/5 bg-slate-800/60 p-4"
          >
            <p className="font-medium capitalize">
              {sim.type.replace("_", " ")}
            </p>

            <p className="mt-2 text-sm text-slate-400 leading-relaxed">
              {sim.explanation}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}