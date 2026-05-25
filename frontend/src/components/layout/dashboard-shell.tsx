import { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { CommandPalette } from "./command-palette";

export function DashboardShell({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      <CommandPalette />
      <div className="flex">
        <Sidebar />

        <main className="min-h-screen flex-1">
          <Topbar />

          <div className="mx-auto max-w-[1600px] px-8 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}