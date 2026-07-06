export type ProjectStatus = "planned" | "active" | "on_hold" | "completed" | "at_risk";
export type ProjectPriority = "low" | "medium" | "high" | "urgent";
export type ProjectTaskStatus = "todo" | "in_progress" | "review" | "done";

export interface ProjectOwner {
  id: string;
  name: string;
  initials: string;
}

export interface ProjectSummary {
  id: string;
  key: string;
  name: string;
  description: string;
  status: ProjectStatus;
  priority: ProjectPriority;
  progress: number;
  openTasks: number;
  completedTasks: number;
  dueDate: string;
  repository: string;
  aiRiskScore: number;
  owner: ProjectOwner;
}

export interface ProjectMilestone {
  id: string;
  title: string;
  dueDate: string;
  status: "complete" | "active" | "blocked" | "upcoming";
}

export interface ProjectTaskPreview {
  id: string;
  key: string;
  title: string;
  assignee: ProjectOwner;
  status: ProjectTaskStatus;
  priority: ProjectPriority;
}

export interface ProjectCommitSignal {
  id: string;
  sha: string;
  message: string;
  author: string;
  time: string;
}

export interface ProjectAiNote {
  id: string;
  title: string;
  detail: string;
  confidence: number;
}

export interface ProjectDetail extends ProjectSummary {
  healthSummary: string;
  sprintGoal: string;
  members: ProjectOwner[];
  milestones: ProjectMilestone[];
  tasks: ProjectTaskPreview[];
  commits: ProjectCommitSignal[];
  aiNotes: ProjectAiNote[];
}

export interface ProjectFilters {
  search?: string;
  status?: ProjectStatus | "all";
}

export interface CreateProjectInput {
  key: string;
  name: string;
  description: string;
  priority: ProjectPriority;
  dueDate: string;
}