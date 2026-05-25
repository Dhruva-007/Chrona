"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Bot,
  Brain,
  Loader2,
  ShieldCheck,
} from "lucide-react";

import { runAgentAnalysis } from "@/lib/api";
import {
  agentStore,
  AgentAnalysisResult,
} from "@/lib/agent-store";
import {
  providerStore,
  Provider,
} from "@/lib/provider-store";

export function AIAgentConsole() {
  const [loading, setLoading] = useState(false);

  const [result, setResult] =
    useState<AgentAnalysisResult | null>(null);

  const [provider, setProvider] =
    useState<Provider>(
      providerStore.getProvider()
    );

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    const syncAgent = () => {
      const state = agentStore.getState();
      setLoading(state.loading);
      setResult(state.result);
    };

    const syncProvider = () => {
      setProvider(
        providerStore.getProvider()
      );
    };

    syncAgent();
    syncProvider();

    const unsubscribeAgent =
      agentStore.subscribe(syncAgent);

    const unsubscribeProvider =
      providerStore.subscribe(
        syncProvider
      );

    return () => {
      unsubscribeAgent();
      unsubscribeProvider();
    };
  }, []);

  async function handleAnalyze() {
    agentStore.setLoading(true);
    setError(null);

    try {
      const res =
        await runAgentAnalysis(
          provider
        );

      agentStore.setResult(res.data);
    } catch (err) {
      console.error(err);

      setError(
        "AI analysis failed. Verify telemetry connectors and backend provider configuration."
      );

      agentStore.setLoading(false);
    }
  }

  function handleProviderChange(
    value: Provider
  ) {
    setProvider(value);
    providerStore.setProvider(value);

    agentStore.setResult(null);
    setError(null);
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="gradient-blue rounded-2xl p-3 text-white shadow-sm">
              <Bot size={20} />
            </div>

            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                Chrona AI Agent
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Autonomous incident investigation
              </p>
            </div>
          </div>

          <select
            value={provider}
            onChange={(e) =>
              handleProviderChange(
                e.target.value as Provider
              )
            }
            disabled={loading}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 outline-none transition hover:border-sky-300"
          >
            <option value="datadog">
              Datadog
            </option>

            <option value="grafana">
              Grafana
            </option>

            <option value="newrelic">
              New Relic
            </option>
          </select>
        </div>
      </div>

      <div className="p-6">
        {!result && !loading && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="text-lg font-medium text-slate-900">
                No AI investigation executed yet
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Selected provider:{" "}
                <span className="font-semibold capitalize">
                  {provider}
                </span>
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Awaiting telemetry ingestion and AI execution
              </p>
            </div>

            {error && (
              <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4">
                <AlertCircle
                  size={18}
                  className="mt-0.5 text-red-600"
                />

                <p className="text-sm leading-relaxed text-red-700">
                  {error}
                </p>
              </div>
            )}

            <button
              onClick={handleAnalyze}
              className="gradient-blue flex w-full items-center justify-center gap-3 rounded-2xl px-5 py-4 font-medium text-white shadow-sm"
            >
              <Brain size={18} />
              Analyze Incident with AI Agent
            </button>
          </div>
        )}

        {loading && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <Loader2
                size={18}
                className="animate-spin text-sky-600"
              />

              <p className="font-medium text-slate-900">
                AI investigation in progress ({provider})
              </p>
            </div>

            {[
              "Inspecting telemetry sources...",
              "Parsing infrastructure dependency graph...",
              "Running deterministic root cause analysis...",
              "Executing counterfactual simulations...",
              "Consulting Groq AI reasoning engine...",
            ].map((step) => (
              <div
                key={step}
                className="animate-pulse rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600"
              >
                {step}
              </div>
            ))}
          </div>
        )}

        {result && (
          <div className="space-y-6">
            <div className="card-hover rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
                Root Cause
              </p>

              <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">
                {result.root_cause}
              </p>

              <p className="mt-3 text-sm text-slate-600">
                Confidence:{" "}
                {Math.round(
                  result.confidence * 100
                )}
                %
              </p>
            </div>

            <section>
              <h3 className="text-base font-semibold text-slate-900">
                Reasoning
              </h3>

              <div className="mt-4 space-y-3">
                {result.reasoning.map(
                  (item) => (
                    <div
                      key={item}
                      className="card-hover rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700"
                    >
                      {item}
                    </div>
                  )
                )}
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-slate-900">
                Recommended Actions
              </h3>

              <div className="mt-4 space-y-3">
                {result.recommended_actions.map(
                  (item) => (
                    <div
                      key={item}
                      className="card-hover flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700"
                    >
                      <ShieldCheck
                        size={16}
                        className="mt-0.5 text-emerald-600"
                      />

                      <span>{item}</span>
                    </div>
                  )
                )}
              </div>
            </section>

            <div className="card-hover rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <h3 className="text-base font-semibold text-slate-900">
                Executive AI Summary
              </h3>

              <p className="mt-4 text-sm leading-7 text-slate-700">
                {result.ai_summary}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}