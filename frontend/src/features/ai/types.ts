export type AiMode = "task_breakdown" | "documentation" | "sprint_planning" | "daily_summary";

export interface AiPromptInput {
  mode: AiMode;
  projectContext: string;
  prompt: string;
}

export interface AiArtifactSection {
  title: string;
  items: string[];
}

export interface AiArtifact {
  id: string;
  mode: AiMode;
  title: string;
  summary: string;
  sections: AiArtifactSection[];
  confidence: number;
  createdAt: string;
}

export interface AiActivityItem {
  id: string;
  mode: AiMode;
  title: string;
  createdAt: string;
  accepted: boolean;
}