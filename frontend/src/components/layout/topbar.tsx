"use client";

import { Bell, Bot } from "lucide-react";

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="flex items-center justify-between px-8 py-5">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">
            Incident Operations Center
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Real-time AI incident response platform
          </p>
        </div>

        <div className="flex items-center gap-4">
          <button className="rounded-2xl border border-slate-200 bg-white p-3 hover:bg-slate-50">
            <Bell size={18} />
          </button>

          <div className="flex items-center gap-3 rounded-2xl bg-sky-600 px-5 py-3 text-white shadow-sm">
            <Bot size={18} />
            Chrona Agent Active
          </div>
        </div>
      </div>
    </header>
  );
}