"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  Activity,
  AlertTriangle,
  Database,
  Loader2,
} from "lucide-react";

import { fetchTelemetry } from "@/lib/api";

import {
  providerStore,
} from "@/lib/provider-store";

import {
  telemetryStore,
} from "@/lib/telemetry-store";

import {
  TelemetryResponse,
} from "@/lib/types";

function badgeColor(
  severity: string
) {
  if (severity === "critical") {
    return "bg-red-100 text-red-700";
  }

  if (severity === "warning") {
    return "bg-amber-100 text-amber-700";
  }

  return "bg-sky-100 text-sky-700";
}

function iconForService(
  service: string
) {
  const s =
    service.toLowerCase();

  if (s.includes("postgres")) {
    return Database;
  }

  if (s.includes("gateway")) {
    return Activity;
  }

  return AlertTriangle;
}

export function TelemetryFeed() {
  const [
    telemetry,
    setTelemetry,
  ] =
    useState<TelemetryResponse | null>(
      null
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  async function loadTelemetry() {
    try {
      const provider =
        providerStore.getProvider();

      const data =
        await fetchTelemetry(provider);

      setTelemetry(data);
      telemetryStore.setTelemetry(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTelemetry();

    const interval =
      setInterval(
        loadTelemetry,
        10000
      );

    const unsubscribe =
      providerStore.subscribe(
        loadTelemetry
      );

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <Loader2
            size={18}
            className="animate-spin text-sky-600"
          />

          <span className="text-sm text-slate-600">
            Connecting to monitoring provider...
          </span>
        </div>
      </div>
    );
  }

  if (!telemetry) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        No telemetry available
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Live Telemetry Feed
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Source: {telemetry.data.source}
            </p>
          </div>

          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase text-emerald-700">
            Live
          </span>
        </div>
      </div>

      <div className="space-y-4 p-6">
        {telemetry.data.alerts.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
            No active alerts
          </div>
        ) : (
          telemetry.data.alerts.map(
            (alert) => {
              const Icon =
                iconForService(
                  alert.service
                );

              return (
                <div
                  key={`${alert.service}-${alert.timestamp}`}
                  className="card-hover flex items-start gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-5"
                >
                  <div className="rounded-xl border border-slate-200 bg-white p-3">
                    <Icon size={18} />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${badgeColor(
                          alert.severity
                        )}`}
                      >
                        {alert.severity}
                      </span>

                      <span className="font-semibold text-slate-900">
                        {alert.service}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-relaxed text-slate-600">
                      {alert.message}
                    </p>
                  </div>
                </div>
              );
            }
          )
        )}
      </div>
    </div>
  );
}