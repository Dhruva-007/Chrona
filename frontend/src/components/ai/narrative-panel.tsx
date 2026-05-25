"use client";

import { useEffect, useState, type ReactNode } from "react";
import {
  Brain,
  ChevronRight,
  Clock3,
  FileText,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { agentStore, AgentAnalysisResult } from "@/lib/agent-store";

interface TimelineEvent {
  timestamp: string;
  node_name: string;
  message: string;
  severity: string;
}

interface PostmortemData {
  incident_overview: {
    title: string;
    description: string;
    severity: string;
    status: string;
  };
  root_cause: {
    node: string;
    confidence: number;
    explanation: string;
  };
  timeline: TimelineEvent[];
  immediate_actions: string[];
  preventive_actions: string[];
  lessons_learned: string[];
}

interface PostmortemResponse {
  success: boolean;
  data: PostmortemData;
}

interface Props {
  postmortem: PostmortemResponse;
}

export function NarrativePanel({ postmortem }: Props) {
  const [open, setOpen] = useState(false);
  const [result, setResult] = useState<AgentAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const sync = () => {
      const state = agentStore.getState();
      setResult(state.result);
      setLoading(state.loading);
    };

    sync();

    return agentStore.subscribe(sync);
  }, []);

  const postmortemData = postmortem.data;

  return (
    <>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <div className="flex items-center gap-3">
              <Brain size={22} className="text-sky-600" />

              <div>
                <h2 className="text-xl font-semibold text-slate-900">
                  AI Incident Summary
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Executive incident intelligence
                </p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {!result && !loading && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                <p className="font-medium text-slate-900">
                  No AI summary available yet
                </p>

                <p className="mt-2 text-sm text-slate-500">
                  Run the Chrona AI Agent to generate incident intelligence
                </p>
              </div>
            )}

            {loading && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center">
                <p className="font-medium text-slate-900">
                  Generating executive summary...
                </p>
              </div>
            )}

            {result && (
              <>
                <p className="text-base leading-8 text-slate-700">
                  {result.ai_summary}
                </p>

                <div className="mt-8 grid grid-cols-3 gap-4">
                  <Metric label="Root Cause" value={result.root_cause} />

                  <Metric
                    label="Confidence"
                    value={`${Math.round(result.confidence * 100)}%`}
                  />

                  <Metric
                    label="Actions"
                    value={String(result.recommended_actions.length)}
                  />
                </div>
              </>
            )}
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <div className="flex items-center gap-3">
              <FileText size={22} className="text-sky-600" />

              <div>
                <h2 className="text-xl font-semibold text-slate-900">
                  Automated Postmortem
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Generated after investigation
                </p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {!result ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
                <p className="font-medium text-slate-900">
                  Postmortem unavailable
                </p>

                <p className="mt-2 text-sm text-slate-500">
                  Execute AI analysis first
                </p>
              </div>
            ) : (
              <>
                <div className="space-y-4">
                  <QuickStat
                    icon={<ShieldAlert size={16} />}
                    title="Severity"
                    value={postmortemData.incident_overview.severity}
                  />

                  <QuickStat
                    icon={<Clock3 size={16} />}
                    title="Timeline Events"
                    value={String(postmortemData.timeline.length)}
                  />

                  <QuickStat
                    icon={<Sparkles size={16} />}
                    title="Preventive Actions"
                    value={String(
                      postmortemData.preventive_actions.length
                    )}
                  />
                </div>

                <button
                  onClick={() => setOpen(true)}
                  className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-sky-600 px-5 py-4 font-medium text-white transition hover:bg-sky-700"
                >
                  View Full Postmortem
                  <ChevronRight size={18} />
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {open && (
        <PostmortemDrawer
          postmortem={postmortemData}
          onClose={() => setOpen(false)}
        />
      )}
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
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-lg font-semibold text-slate-900">
        {value}
      </p>
    </div>
  );
}

function QuickStat({
  icon,
  title,
  value,
}: {
  icon: ReactNode;
  title: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
      <div className="flex items-center gap-3 text-slate-700">
        {icon}
        <span>{title}</span>
      </div>

      <span className="font-semibold text-slate-900">
        {value}
      </span>
    </div>
  );
}

function PostmortemDrawer({
  postmortem,
  onClose,
}: {
  postmortem: PostmortemData;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm">
      <div className="absolute right-0 top-0 h-screen w-[760px] overflow-y-auto border-l border-slate-200 bg-white shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">
              Incident Postmortem
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              AI-generated forensic report
            </p>
          </div>

          <button
            onClick={onClose}
            className="rounded-xl border border-slate-200 p-2 text-slate-700 hover:bg-slate-100"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-8 p-6">
          <Section
            title="Incident Overview"
            content={postmortem.incident_overview.description}
          />

          <Section
            title="Root Cause"
            content={postmortem.root_cause.explanation}
          />

          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              Timeline
            </h3>

            <div className="mt-4 space-y-4">
              {postmortem.timeline.map((event, index) => (
                <div
                  key={`${event.node_name}-${index}`}
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
                >
                  <p className="text-xs text-slate-500">
                    {event.timestamp}
                  </p>

                  <p className="mt-2 font-medium text-slate-900">
                    {event.node_name}
                  </p>

                  <p className="mt-2 text-sm leading-relaxed text-slate-700">
                    {event.message}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <ListSection
            title="Immediate Actions"
            items={postmortem.immediate_actions}
          />

          <ListSection
            title="Preventive Actions"
            items={postmortem.preventive_actions}
          />

          <ListSection
            title="Lessons Learned"
            items={postmortem.lessons_learned}
          />
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  content,
}: {
  title: string;
  content: string;
}) {
  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-900">
        {title}
      </h3>

      <p className="mt-3 text-sm leading-relaxed text-slate-700">
        {content}
      </p>
    </div>
  );
}

function ListSection({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-900">
        {title}
      </h3>

      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div
            key={item}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700"
          >
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}