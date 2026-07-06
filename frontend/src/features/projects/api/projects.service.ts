import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { CreateProjectInput, ProjectDetail, ProjectFilters, ProjectSummary } from "../types";


let mockProjects: ProjectSummary[] = [
  {
    id: "project_core_api",
    key: "CORE",
    name: "Core API Reliability",
    description: "Connection pooling, session handling, and audit-ready persistence for the FastAPI backend.",
    status: "active",
    priority: "urgent",
    progress: 82,
    openTasks: 14,
    completedTasks: 49,
    dueDate: "2026-07-12",
    repository: "devtrack/core-api",
    aiRiskScore: 18,
    owner: { id: "u1", name: "Avery Chen", initials: "AC" },
  },
  {
    id: "project_kanban_realtime",
    key: "KAN",
    name: "Realtime Kanban Moves",
    description: "Ordering, status transitions, and drag-and-drop persistence for task boards.",
    status: "at_risk",
    priority: "high",
    progress: 61,
    openTasks: 21,
    completedTasks: 32,
    dueDate: "2026-07-10",
    repository: "devtrack/web-app",
    aiRiskScore: 41,
    owner: { id: "u2", name: "Mira Patel", initials: "MP" },
  },
  {
    id: "project_github_sync",
    key: "GIT",
    name: "GitHub Metadata Sync",
    description: "OAuth, repository indexing, commits, issues, and pull request metadata ingestion.",
    status: "active",
    priority: "high",
    progress: 74,
    openTasks: 9,
    completedTasks: 27,
    dueDate: "2026-07-16",
    repository: "devtrack/integrations",
    aiRiskScore: 22,
    owner: { id: "u3", name: "Noah Kim", initials: "NK" },
  },
  {
    id: "project_ai_planner",
    key: "AI",
    name: "AI Sprint Planner",
    description: "Gemini-backed sprint plans, task breakdowns, documentation, and daily summaries.",
    status: "on_hold",
    priority: "medium",
    progress: 43,
    openTasks: 17,
    completedTasks: 18,
    dueDate: "2026-07-22",
    repository: "devtrack/ai-services",
    aiRiskScore: 63,
    owner: { id: "u4", name: "Sam Rivera", initials: "SR" },
  },
];

const members = [
  { id: "u1", name: "Avery Chen", initials: "AC" },
  { id: "u2", name: "Mira Patel", initials: "MP" },
  { id: "u3", name: "Noah Kim", initials: "NK" },
  { id: "u4", name: "Sam Rivera", initials: "SR" },
];

function applyFilters(projects: ProjectSummary[], filters: ProjectFilters): ProjectSummary[] {
  const search = filters.search?.trim().toLowerCase();
  return projects.filter((project) => {
    const matchesSearch = !search || [project.key, project.name, project.description, project.repository].some((value) => value.toLowerCase().includes(search));
    const matchesStatus = !filters.status || filters.status === "all" || project.status === filters.status;
    return matchesSearch && matchesStatus;
  });
}

function buildProjectDetail(project: ProjectSummary): ProjectDetail {
  const isKanban = project.key === "KAN";
  const isAi = project.key === "AI";

  return {
    ...project,
    healthSummary: isAi
      ? "Planning quality is good, but model evaluation and UI review are moving independently. Split the workstream before the next sprint review."
      : isKanban
        ? "Drag-and-drop ordering is the main delivery risk. Backend move semantics are ready, but UI acceptance cases still need coverage."
        : "Delivery is healthy. Remaining work is mostly verification, integration hardening, and documentation cleanup.",
    sprintGoal: isKanban
      ? "Ship realtime-ready task movement with deterministic ordering and optimistic updates."
      : isAi
        ? "Turn AI planning into reviewable, auditable project artifacts."
        : "Stabilize the production path and reduce operational ambiguity before release.",
    members,
    milestones: [
      { id: "m1", title: "Scope locked", dueDate: "2026-07-04", status: "complete" },
      { id: "m2", title: "Backend contract verified", dueDate: "2026-07-08", status: isAi ? "blocked" : "active" },
      { id: "m3", title: "Frontend acceptance review", dueDate: "2026-07-11", status: "upcoming" },
      { id: "m4", title: "Release candidate", dueDate: project.dueDate, status: "upcoming" },
    ],
    tasks: [
      { id: "t1", key: `${project.key}-118`, title: "Validate service-layer contract", assignee: members[0], status: "in_progress", priority: "high" },
      { id: "t2", key: `${project.key}-119`, title: "Add UI acceptance states", assignee: members[1], status: "review", priority: project.priority },
      { id: "t3", key: `${project.key}-120`, title: "Document rollback path", assignee: members[2], status: "todo", priority: "medium" },
      { id: "t4", key: `${project.key}-121`, title: "Close analytics instrumentation", assignee: members[3], status: "done", priority: "low" },
    ],
    commits: [
      { id: "c1", sha: "9f3a21c", message: "Tighten repository query boundaries", author: "Noah Kim", time: "18 min ago" },
      { id: "c2", sha: "c41d8aa", message: "Add optimistic state handoff", author: "Mira Patel", time: "1 hr ago" },
      { id: "c3", sha: "7b8e004", message: "Normalize audit metadata", author: "Avery Chen", time: "3 hrs ago" },
    ],
    aiNotes: [
      { id: "a1", title: "Narrow the next review", detail: "Most incomplete tasks share the same dependency: acceptance rules for status transitions.", confidence: 89 },
      { id: "a2", title: "Watch deadline compression", detail: "Open task count is still high relative to the due date and review workload.", confidence: project.aiRiskScore > 40 ? 92 : 74 },
    ],
  };
}

export const projectsService = {
  async listProjects(workspaceId: string, filters: ProjectFilters): Promise<ProjectSummary[]> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(300);
      return applyFilters(mockProjects, filters);
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<ProjectSummary[]>(`/workspaces/${workspaceId}/projects`, { params: filters });
    return response.data;
  },

  async getProject(workspaceId: string, projectId: string): Promise<ProjectDetail> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(280);
      const project = mockProjects.find((item) => item.id === projectId) ?? mockProjects[0];
      return buildProjectDetail(project);
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<ProjectDetail>(`/workspaces/${workspaceId}/projects/${projectId}`);
    return response.data;
  },

  async createProject(workspaceId: string, input: CreateProjectInput): Promise<ProjectSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(400);
      const created: ProjectSummary = {
        id: `project_${input.key.toLowerCase()}_${Date.now()}`,
        key: input.key.toUpperCase(),
        name: input.name,
        description: input.description,
        status: "planned",
        priority: input.priority,
        progress: 0,
        openTasks: 0,
        completedTasks: 0,
        dueDate: input.dueDate,
        repository: "Not connected",
        aiRiskScore: 12,
        owner: { id: "u1", name: "Avery Chen", initials: "AC" },
      };
      mockProjects = [created, ...mockProjects];
      return created;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.post<ProjectSummary>(`/workspaces/${workspaceId}/projects`, input);
    return response.data;
  },
};


