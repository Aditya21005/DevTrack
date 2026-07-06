import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { AiActivityItem, AiArtifact, AiMode, AiPromptInput } from "../types";


let mockHistory: AiActivityItem[] = [
  { id: "ai_1", mode: "task_breakdown", title: "Realtime kanban ordering breakdown", createdAt: "18 min ago", accepted: true },
  { id: "ai_2", mode: "documentation", title: "GitHub OAuth setup notes", createdAt: "1 hr ago", accepted: true },
  { id: "ai_3", mode: "daily_summary", title: "Release hardening daily summary", createdAt: "3 hrs ago", accepted: false },
];

const modeTitles: Record<AiMode, string> = {
  task_breakdown: "Task Breakdown",
  documentation: "Documentation Draft",
  sprint_planning: "Sprint Plan",
  daily_summary: "Daily Summary",
};

function buildMockArtifact(input: AiPromptInput): AiArtifact {
  const title = `${modeTitles[input.mode]}: ${input.projectContext}`;
  const baseItems = input.prompt
    .split(/[.\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3);

  const fallback = ["Confirm scope with the project owner", "Identify dependencies", "Create reviewable follow-up tasks"];
  const items = baseItems.length ? baseItems : fallback;

  const sectionsByMode: Record<AiMode, AiArtifact["sections"]> = {
    task_breakdown: [
      { title: "Implementation Steps", items: items.map((item) => `Turn '${item}' into a scoped engineering task`) },
      { title: "Acceptance Criteria", items: ["Each task has owner, priority, and status", "Dependencies are explicit", "Review path is clear"] },
      { title: "Risks", items: ["Hidden backend contract drift", "Unclear definition of done"] },
    ],
    documentation: [
      { title: "Outline", items: ["Purpose", "Configuration", "Operational flow", "Failure handling"] },
      { title: "Key Notes", items: items.map((item) => `Document: ${item}`) },
      { title: "Reviewer Checklist", items: ["Examples compile", "Environment variables are named", "Security assumptions are stated"] },
    ],
    sprint_planning: [
      { title: "Recommended Scope", items },
      { title: "Sequence", items: ["Unblock dependencies", "Complete implementation", "Reserve review capacity"] },
      { title: "Defer", items: ["Low confidence work", "Non-critical polish", "Unowned tasks"] },
    ],
    daily_summary: [
      { title: "Completed", items: items.slice(0, 2) },
      { title: "In Progress", items: ["Project coordination", "Review queue cleanup"] },
      { title: "Blockers", items: ["Waiting on final acceptance feedback"] },
    ],
  };

  return {
    id: `artifact_${Date.now()}`,
    mode: input.mode,
    title,
    summary: "Generated from workspace context with assumptions kept explicit and output shaped for engineering review.",
    sections: sectionsByMode[input.mode],
    confidence: input.mode === "sprint_planning" ? 84 : 89,
    createdAt: "just now",
  };
}

export const aiService = {
  async listHistory(workspaceId: string): Promise<AiActivityItem[]> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(220);
      return mockHistory;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<AiActivityItem[]>(`/workspaces/${workspaceId}/ai/history`);
    return response.data;
  },

  async generateArtifact(workspaceId: string, input: AiPromptInput): Promise<AiArtifact> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(650);
      const artifact = buildMockArtifact(input);
      mockHistory = [{ id: artifact.id, mode: artifact.mode, title: artifact.title, createdAt: artifact.createdAt, accepted: false }, ...mockHistory];
      return artifact;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.post<AiArtifact>(`/workspaces/${workspaceId}/ai/generate`, input);
    return response.data;
  },
};


