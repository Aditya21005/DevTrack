import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { DashboardSummary } from "../types";


const mockDashboardSummary: DashboardSummary = {
  workspaceName: "Platform Engineering",
  sprintName: "Sprint 24.7 - Release hardening",
  metrics: [
    { id: "velocity", label: "Velocity", value: "78 pts", delta: "+12% vs last sprint", tone: "primary" },
    { id: "completed", label: "Completed", value: "142", delta: "31 this week", tone: "success" },
    { id: "pending", label: "Pending", value: "36", delta: "8 need triage", tone: "warning" },
    { id: "ai", label: "AI assists", value: "219", delta: "43 accepted", tone: "accent" },
  ],
  projects: [
    { id: "p1", key: "CORE", name: "Core API Reliability", status: "on-track", progress: 82, openTasks: 14, dueLabel: "Due Jul 12" },
    { id: "p2", key: "KAN", name: "Realtime Kanban Moves", status: "at-risk", progress: 61, openTasks: 21, dueLabel: "Due Jul 10" },
    { id: "p3", key: "GIT", name: "GitHub Metadata Sync", status: "on-track", progress: 74, openTasks: 9, dueLabel: "Due Jul 16" },
    { id: "p4", key: "AI", name: "AI Sprint Planner", status: "blocked", progress: 43, openTasks: 17, dueLabel: "Blocked" },
  ],
  activity: [
    { id: "a1", title: "PR #482 merged", detail: "OAuth callback lock window reduced", time: "12 min ago", tone: "success" },
    { id: "a2", title: "AI generated 7 subtasks", detail: "Realtime board ordering epic", time: "28 min ago", tone: "accent" },
    { id: "a3", title: "3 tasks need owners", detail: "Release hardening lane", time: "46 min ago", tone: "warning" },
    { id: "a4", title: "Repository sync finished", detail: "18 repos, 312 commits indexed", time: "1 hr ago", tone: "primary" },
  ],
  recommendations: [
    { id: "r1", title: "Split blocked AI planner task", detail: "The model integration and UX review are moving at different speeds.", confidence: 91 },
    { id: "r2", title: "Pull KAN-118 into active sprint", detail: "It unblocks two review tasks and has a low dependency count.", confidence: 86 },
    { id: "r3", title: "Schedule API load-test follow-up", detail: "Commit volume rose while reliability tasks stayed flat.", confidence: 78 },
  ],
  monthlyStats: [
    { month: "Feb", completed: 88, pending: 42 },
    { month: "Mar", completed: 104, pending: 38 },
    { month: "Apr", completed: 97, pending: 44 },
    { month: "May", completed: 126, pending: 35 },
    { month: "Jun", completed: 138, pending: 31 },
    { month: "Jul", completed: 142, pending: 36 },
  ],
  github: {
    repositories: 18,
    pullRequests: 27,
    commitsToday: 64,
    syncStatus: "healthy",
    lastSyncedAt: "4 minutes ago",
  },
};

export const dashboardService = {
  async getSummary(workspaceId: string): Promise<DashboardSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(350);
      return mockDashboardSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<DashboardSummary>(`/workspaces/${workspaceId}/dashboard`);
    return response.data;
  },
};


