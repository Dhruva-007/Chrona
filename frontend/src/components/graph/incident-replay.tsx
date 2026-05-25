"use client";

import { Pause, Play, RotateCcw } from "lucide-react";

interface Props {
  currentStep: number;
  maxSteps: number;
  isPlaying: boolean;
  onPlayPause: () => void;
  onReset: () => void;
  onStepChange: (step: number) => void;
}

const LABELS = [
  "Healthy baseline",
  "PostgreSQL failure",
  "Payment degradation",
  "Order cascade",
  "Gateway impact",
  "Full outage",
];

export function IncidentReplay({
  currentStep,
  maxSteps,
  isPlaying,
  onPlayPause,
  onReset,
  onStepChange,
}: Props) {
  return (
    <div className="mb-6 rounded-2xl border border-white/5 bg-slate-900/70 p-5">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">
            Incident Replay
          </h3>

          <p className="mt-1 text-sm text-slate-400">
            Time-travel through cascading failure propagation
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onPlayPause}
            className="rounded-xl border border-slate-700 bg-slate-800 p-3 text-slate-200 hover:bg-slate-700 transition"
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>

          <button
            onClick={onReset}
            className="rounded-xl border border-slate-700 bg-slate-800 p-3 text-slate-200 hover:bg-slate-700 transition"
          >
            <RotateCcw size={18} />
          </button>
        </div>
      </div>

      <div className="mt-6">
        <input
          type="range"
          min={0}
          max={maxSteps}
          value={currentStep}
          onChange={(e) => onStepChange(Number(e.target.value))}
          className="w-full"
        />

        <div className="mt-3 flex items-center justify-between text-sm text-slate-400">
          <span>T+{currentStep * 30}s</span>
          <span>{LABELS[currentStep]}</span>
        </div>
      </div>
    </div>
  );
}