"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import {
  Activity,
  AlertTriangle,
  Bot,
  FileText,
  LayoutDashboard,
  Search,
  Settings,
  Wifi,
} from "lucide-react";

import {
  providerStore,
  Provider,
} from "@/lib/provider-store";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    section: "Operations",
  },
  {
    label: "Incidents",
    href: "/incidents",
    icon: AlertTriangle,
    section: "Operations",
  },
  {
    label: "Telemetry",
    href: "/telemetry",
    icon: Activity,
    section: "Monitoring",
  },
  {
    label: "AI Agent",
    href: "/ai-agent",
    icon: Bot,
    section: "AI Intelligence",
  },
  {
    label: "Postmortems",
    href: "/postmortems",
    icon: FileText,
    section: "AI Intelligence",
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
    section: "System",
  },
];

const sections = [
  "Operations",
  "Monitoring",
  "AI Intelligence",
  "System",
];

function providerLabel(provider: Provider) {
  if (provider === "newrelic") {
    return "New Relic";
  }

  if (provider === "grafana") {
    return "Grafana";
  }

  return "Datadog";
}

export function Sidebar() {
  const pathname = usePathname();

  const [provider, setProvider] =
    useState<Provider>(
      providerStore.getProvider()
    );

  useEffect(() => {
    return providerStore.subscribe(() => {
      setProvider(
        providerStore.getProvider()
      );
    });
  }, []);

  return (
    <aside className="sticky top-0 flex h-screen w-[300px] flex-col border-r border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-sky-600 text-xl font-bold text-white shadow-sm">
            C
          </div>

          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
              Chrona
            </h1>

            <p className="text-sm text-slate-500">
              AI Incident Intelligence
            </p>
          </div>
        </div>
      </div>

      <div className="border-b border-slate-200 px-6 py-5">
        <button
          onClick={() => {
            window.dispatchEvent(
              new KeyboardEvent(
                "keydown",
                {
                  key: "k",
                  ctrlKey: true,
                }
              )
            );
          }}
          className="flex w-full items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:bg-white"
        >
          <Search
            size={18}
            className="text-slate-400"
          />

          <span className="flex-1 text-sm text-slate-500">
            Search incidents, telemetry...
          </span>

          <span className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs text-slate-500">
            Ctrl K
          </span>
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-4 py-6">
        <div className="space-y-8">
          {sections.map((section) => {
            const items =
              navItems.filter(
                (item) =>
                  item.section === section
              );

            return (
              <div
                key={section}
                className="space-y-2"
              >
                <p className="px-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">
                  {section}
                </p>

                {items.map((item) => {
                  const Icon =
                    item.icon;

                  const active =
                    pathname ===
                    item.href;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-4 rounded-2xl px-4 py-4 transition ${
                        active
                          ? "bg-sky-600 text-white shadow-sm"
                          : "text-slate-700 hover:bg-slate-100"
                      }`}
                    >
                      <Icon
                        size={20}
                      />

                      <span className="font-medium">
                        {item.label}
                      </span>
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-slate-200 p-5">
        <div className="rounded-3xl border border-sky-100 bg-sky-50 p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-white p-3 shadow-sm">
              <Wifi
                size={18}
                className="text-sky-600"
              />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Monitoring
              </p>

              <p className="mt-1 font-semibold text-slate-900">
                {providerLabel(provider)}
              </p>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between rounded-2xl border border-white bg-white px-4 py-3">
            <span className="text-sm text-slate-600">
              Telemetry Status
            </span>

            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase text-emerald-700">
              Live
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}