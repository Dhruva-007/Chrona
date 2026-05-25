"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  X,
  ShieldCheck,
} from "lucide-react";

import {
  InfrastructureNode,
  TelemetryResponse,
} from "@/lib/types";

import {
  agentStore,
  AgentAnalysisResult,
} from "@/lib/agent-store";

import {
  telemetryStore,
} from "@/lib/telemetry-store";

interface Props {
  node: InfrastructureNode | null;
  telemetry: TelemetryResponse;
  onClose: () => void;
}

function buildDynamicDiagnosis(
  node: InfrastructureNode,
  telemetry: TelemetryResponse,
  agentResult: AgentAnalysisResult | null
) {
  const metric =
    telemetry.data.metrics[node.id];

  const findings: string[] = [];

  if (metric) {
    if (metric.cpu_percent > 85) {
      findings.push(
        `CPU utilization elevated at ${metric.cpu_percent}%`
      );
    }

    if (metric.memory_percent > 80) {
      findings.push(
        `Memory pressure detected at ${metric.memory_percent}%`
      );
    }

    if (metric.error_rate > 5) {
      findings.push(
        `Error rate elevated to ${metric.error_rate}%`
      );
    }

    if (metric.latency_ms > 1000) {
      findings.push(
        `Latency degradation observed (${metric.latency_ms}ms)`
      );
    }
  }

  if (
    agentResult &&
    agentResult.root_cause
      .toLowerCase()
      .includes(node.name.toLowerCase())
  ) {
    findings.push(
      "AI agent identified this node as a probable root cause candidate"
    );
  }

  if (findings.length === 0) {
    findings.push(
      "No critical telemetry anomalies detected for this node"
    );
  }

  const actions: string[] = [];

  if (metric?.cpu_percent > 85) {
    actions.push(
      "Investigate compute saturation and autoscaling thresholds"
    );
  }

  if (metric?.error_rate > 5) {
    actions.push(
      "Inspect application logs and upstream dependency failures"
    );
  }

  if (metric?.latency_ms > 1000) {
    actions.push(
      "Analyze latency bottlenecks and downstream timeouts"
    );
  }

  if (
    agentResult &&
    agentResult.root_cause
      .toLowerCase()
      .includes(node.name.toLowerCase())
  ) {
    actions.push(
      "Prioritize remediation for this AI-identified root cause"
    );
  }

  if (actions.length === 0) {
    actions.push(
      "Continue active monitoring"
    );
  }

  return {
    diagnosis: findings.join(". "),
    actions,
  };
}

export function NodeInspector({
  node,
  telemetry,
  onClose,
}: Props) {
  const [
    liveTelemetry,
    setLiveTelemetry,
  ] = useState<TelemetryResponse | null>(
    telemetryStore.getTelemetry()
  );

  useEffect(() => {
    const unsubscribe =
      telemetryStore.subscribe(() => {
        setLiveTelemetry(
          telemetryStore.getTelemetry()
        );
      });

    return unsubscribe;
  }, []);

  if (!node) {
    return null;
  }

  const activeTelemetry =
    liveTelemetry ?? telemetry;

  const agentResult =
    agentStore.getState().result;

  const insight =
    buildDynamicDiagnosis(
      node,
      activeTelemetry,
      agentResult
    );

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="fixed right-0 top-0 z-50 h-screen w-[500px] overflow-y-auto border-l border-slate-200 bg-white shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
              {node.name}
            </h2>

            <p className="mt-1 text-sm uppercase tracking-wide text-slate-500">
              {node.type}
            </p>
          </div>

          <button
            onClick={onClose}
            className="rounded-2xl border border-slate-200 bg-white p-3 hover:bg-slate-50"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-8 p-6">
          <div className="grid grid-cols-2 gap-4">
            <Metric
              label="CPU"
              value={`${node.cpu_usage}%`}
            />
            <Metric
              label="Memory"
              value={`${node.memory_usage}%`}
            />
            <Metric
              label="Error Rate"
              value={`${node.error_rate}%`}
            />
            <Metric
              label="Latency"
              value={`${node.latency_ms}ms`}
            />
            <Metric
              label="Replicas"
              value={String(node.replicas)}
            />
            <Metric
              label="Version"
              value={node.version}
            />
          </div>

          <section>
            <h3 className="text-base font-semibold text-slate-900">
              Live Diagnosis
            </h3>

            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm leading-7 text-slate-700">
                {insight.diagnosis}
              </p>
            </div>
          </section>

          <section>
            <h3 className="text-base font-semibold text-slate-900">
              Recommended Actions
            </h3>

            <div className="mt-4 space-y-3">
              {insight.actions.map(
                (action) => (
                  <div
                    key={action}
                    className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700"
                  >
                    <ShieldCheck
                      size={16}
                      className="mt-0.5 text-emerald-600"
                    />

                    <span>{action}</span>
                  </div>
                )
              )}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-2xl font-semibold text-slate-900">
        {value}
      </p>
    </div>
  );
}