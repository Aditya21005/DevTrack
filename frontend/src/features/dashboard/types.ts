export interface DashboardMetric {
  id: string;
  label: string;
  value: string;
  delta: string;
  tone: "primary" | "success" | "warning" | "accent";
}

export interface ProjectHealth {
  id: string;
  key: string;
  name: string;
  status: "on-track" | "at-risk" | "blocked";
  progress: number;
  openTasks: number;
  dueLabel: string;
}

export interface ActivitySignal {
  id: string;
  title: string;
  detail: string;
  time: string;
  tone: "primary" | "success" | "warning" | "accent";
}

export interface AiRecommendation {
  id: string;
  title: string;
  detail: string;
  confidence: number;
}

export interface MonthlyStat {
  month: string;
  completed: number;
  pending: number;
}

export interface GithubSignal {
  repositories: number;
  pullRequests: number;
  commitsToday: number;
  syncStatus: "healthy" | "delayed" | "failed";
  lastSyncedAt: string;
}

export interface DashboardSummary {
  workspaceName: string;
  sprintName: string;
  metrics: DashboardMetric[];
  projects: ProjectHealth[];
  activity: ActivitySignal[];
  recommendations: AiRecommendation[];
  monthlyStats: MonthlyStat[];
  github: GithubSignal;
}