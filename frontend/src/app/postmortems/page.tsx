import { DashboardShell } from "@/components/layout/dashboard-shell";
import { NarrativePanel } from "@/components/ai/narrative-panel";
import { fetchPostmortem } from "@/lib/api";

export default async function PostmortemsPage() {
  const postmortem =
    await fetchPostmortem();

  return (
    <DashboardShell>
      <NarrativePanel
        postmortem={postmortem}
      />
    </DashboardShell>
  );
}