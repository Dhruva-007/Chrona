"use client";

interface Props {
  mode: string;
  onChange: (mode: string) => void;
}

const OPTIONS = [
  {
    id: "reality",
    label: "Reality",
  },
  {
    id: "counterfactual",
    label: "Postgres Saved",
  },
  {
    id: "failover",
    label: "Replica Failover",
  },
];

export function SimulationToggle({
  mode,
  onChange,
}: Props) {
  return (
    <div className="mb-6 flex flex-wrap gap-3">
      {OPTIONS.map((option) => {
        const active = mode === option.id;

        return (
          <button
            key={option.id}
            onClick={() => onChange(option.id)}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition ${
              active
                ? "bg-blue-600 text-white"
                : "border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}