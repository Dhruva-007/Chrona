"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import { useRouter } from "next/navigation";

const items = [
  {
    label: "Overview Dashboard",
    href: "/",
    keywords: "overview dashboard home incidents",
  },
  {
    label: "Infrastructure Graph",
    href: "/infrastructure",
    keywords: "graph infra nodes services dependencies",
  },
  {
    label: "Root Cause Analysis",
    href: "/root-cause",
    keywords: "root cause analysis failures investigation",
  },
  {
    label: "Counterfactual Simulations",
    href: "/simulations",
    keywords: "simulation counterfactual what-if recovery",
  },
  {
    label: "Incident Reports",
    href: "/reports",
    keywords: "reports postmortem summaries ai",
  },
  {
    label: "Platform Settings",
    href: "/settings",
    keywords: "settings config integrations",
  },
  {
    label: "postgres-primary",
    href: "/infrastructure",
    keywords: "postgres database db primary",
  },
  {
    label: "payment-svc",
    href: "/root-cause",
    keywords: "payment service failures checkout",
  },
  {
    label: "gateway-01",
    href: "/infrastructure",
    keywords: "gateway ingress latency",
  },
];

export function CommandPalette() {
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }

      if (e.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("keydown", handler);

    return () => {
      window.removeEventListener("keydown", handler);
    };
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return items;

    const q = query.toLowerCase();

    return items.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.keywords.includes(q)
    );
  }, [query]);

  function navigate(href: string) {
    setOpen(false);
    setQuery("");
    router.push(href);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] bg-black/30 backdrop-blur-sm">
      <div className="mx-auto mt-24 w-full max-w-2xl rounded-3xl border border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center gap-4 border-b border-slate-200 px-6 py-5">
          <Search size={20} className="text-slate-400" />

          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search incidents, services, reports..."
            className="w-full bg-transparent text-lg outline-none placeholder:text-slate-400"
          />

          <button
            onClick={() => setOpen(false)}
            className="rounded-xl p-2 hover:bg-slate-100"
          >
            <X size={18} />
          </button>
        </div>

        <div className="max-h-[500px] overflow-y-auto p-3">
          {filtered.map((item) => (
            <button
              key={item.label}
              onClick={() => navigate(item.href)}
              className="flex w-full items-center rounded-2xl px-4 py-4 text-left transition hover:bg-slate-100"
            >
              <div>
                <p className="font-medium text-slate-900">
                  {item.label}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {item.href}
                </p>
              </div>
            </button>
          ))}

          {filtered.length === 0 && (
            <div className="p-8 text-center text-slate-500">
              No matching results
            </div>
          )}
        </div>
      </div>
    </div>
  );
}