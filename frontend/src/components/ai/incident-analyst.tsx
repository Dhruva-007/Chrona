"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Brain,
  FileText,
  Shield,
} from "lucide-react";

import { fetchAgentAnalysis } from "@/lib/api";

interface HealthData {
  critical_nodes: number;
  degraded_nodes: number;
  health_score: number;
}

interface AnalysisResponse {
  success: boolean;
  data: {
    root_cause: string;
    confidence: number;
    reasoning: string[];
    recommended_actions: string[];
    executive_summary: string;
  };
}

interface SimulationResponse {
  data: {
    simulations: {
      replica_failover: {
        confidence: number;
      };
    };
  };
}

interface Props {
  health: HealthData;
  suite: SimulationResponse;
}

function buildFallbackImpact(
  health: HealthData
) {
  return `${health.critical_nodes} critical services and ${health.degraded_nodes} degraded services were impacted. Platform health score dropped to ${Math.round(
    health.health_score
  )}%.`;
}

export function IncidentAnalyst({
  health,
  suite,
}: Props) {
  const [analysis, setAnalysis] =
    useState<AnalysisResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(false);

  async function loadAnalysis() {
    try {
      setLoading(true);

      const result =
        await fetchAgentAnalysis();

      if (result?.success) {
        setAnalysis(result);
      }
    } catch {
      // silent fallback
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalysis();

    const interval =
      setInterval(() => {
        loadAnalysis();
      }, 5000);

    return () =>
      clearInterval(interval);
  }, []);

  const recovery =
    Math.round(
      suite.data.simulations
        .replica_failover.confidence * 100
    );

  return (
    <div className="rounded-3xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-200 px-8 py-6">
        <h2 className="flex items-center gap-3 text-3xl font-semibold text-slate-900">
          <Brain size={28} className="text-sky-600" />
          AI Incident Analyst
        </h2>

        <p className="mt-2 text-slate-500">
          Live AI-generated incident explanation and recovery intelligence
        </p>
      </div>

      {!analysis ? (
        <div className="p-10">
          <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
            <Brain
              size={40}
              className="mx-auto text-slate-400"
            />

            <h3 className="mt-4 text-2xl font-semibold text-slate-900">
              No AI analysis available yet
            </h3>

            <p className="mt-3 text-slate-500">
              Run the Chrona AI Agent to generate executive intelligence,
              remediation guidance, and business impact assessment.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 p-8 md:grid-cols-2">
          <InsightCard
            icon={<Brain size={18} />}
            title="Executive Summary"
            content={
              analysis.data.executive_summary
            }
          />

          <InsightCard
            icon={
              <AlertTriangle size={18} />
            }
            title="Root Cause Narrative"
            content={
              analysis.data.reasoning[0]
            }
          />

          <InsightCard
            icon={<Shield size={18} />}
            title="Business Impact"
            content={buildFallbackImpact(
              health
            )}
          />

          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <div className="flex items-center gap-2">
              <FileText
                size={18}
                className="text-sky-600"
              />

              <h3 className="text-lg font-semibold text-slate-900">
                Recommended Actions
              </h3>
            </div>

            <div className="mt-5 space-y-3">
              {analysis.data.recommended_actions.map(
                (action) => (
                  <div
                    key={action}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm text-slate-700"
                  >
                    {action}
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InsightCard({
  icon,
  title,
  content,
}: {
  icon: React.ReactNode;
  title: string;
  content: string;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
      <div className="flex items-center gap-2">
        <div className="text-sky-600">
          {icon}
        </div>

        <h3 className="text-lg font-semibold text-slate-900">
          {title}
        </h3>
      </div>

      <p className="mt-5 text-base leading-8 text-slate-700">
        {content}
      </p>
    </div>
  );
}