import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { GithubIntegrationSummary } from "../types";


let mockSummary: GithubIntegrationSummary = {
  connection: {
    id: "github_conn_01",
    accountName: "devtrack-ai",
    status: "connected",
    scopes: ["repo", "read:user", "user:email"],
    lastSyncedAt: "4 minutes ago",
  },
  repositories: [
    { id: "repo_1", name: "core-api", fullName: "devtrack/core-api", visibility: "private", language: "Python", defaultBranch: "main", openPullRequests: 7, openIssues: 14, commitsToday: 22, linkedProjectKey: "CORE" },
    { id: "repo_2", name: "web-app", fullName: "devtrack/web-app", visibility: "private", language: "TypeScript", defaultBranch: "main", openPullRequests: 11, openIssues: 21, commitsToday: 31, linkedProjectKey: "KAN" },
    { id: "repo_3", name: "integrations", fullName: "devtrack/integrations", visibility: "private", language: "Python", defaultBranch: "main", openPullRequests: 5, openIssues: 9, commitsToday: 8, linkedProjectKey: "GIT" },
    { id: "repo_4", name: "ai-services", fullName: "devtrack/ai-services", visibility: "private", language: "Python", defaultBranch: "main", openPullRequests: 4, openIssues: 17, commitsToday: 3, linkedProjectKey: "AI" },
  ],
  commits: [
    { id: "commit_1", sha: "9f3a21c", message: "Shorten OAuth state lock window", author: "Noah Kim", repository: "devtrack/integrations", authoredAt: "18 min ago" },
    { id: "commit_2", sha: "c41d8aa", message: "Add optimistic board movement", author: "Mira Patel", repository: "devtrack/web-app", authoredAt: "1 hr ago" },
    { id: "commit_3", sha: "7b8e004", message: "Normalize audit metadata", author: "Avery Chen", repository: "devtrack/core-api", authoredAt: "3 hrs ago" },
    { id: "commit_4", sha: "af29c10", message: "Tune Gemini prompt guardrails", author: "Sam Rivera", repository: "devtrack/ai-services", authoredAt: "5 hrs ago" },
  ],
  issues: [
    { id: "issue_1", number: 142, title: "Document token encryption key rotation", state: "open", labels: ["security", "docs"], repository: "devtrack/integrations", openedAt: "2 hrs ago" },
    { id: "issue_2", number: 118, title: "Board order jumps after rapid moves", state: "open", labels: ["kanban", "frontend"], repository: "devtrack/web-app", openedAt: "6 hrs ago" },
    { id: "issue_3", number: 89, title: "Dashboard monthly chart needs backend endpoint", state: "closed", labels: ["analytics"], repository: "devtrack/core-api", openedAt: "yesterday" },
  ],
  pullRequests: [
    { id: "pr_1", number: 482, title: "Implement GitHub metadata sync service", state: "merged", repository: "devtrack/integrations", author: "Noah Kim", targetBranch: "main", openedAt: "1 day ago" },
    { id: "pr_2", number: 517, title: "Add command-center dashboard cards", state: "open", repository: "devtrack/web-app", author: "Mira Patel", targetBranch: "main", openedAt: "3 hrs ago" },
    { id: "pr_3", number: 529, title: "Draft AI sprint planner workflow", state: "draft", repository: "devtrack/ai-services", author: "Sam Rivera", targetBranch: "main", openedAt: "5 hrs ago" },
  ],
};

export const githubService = {
  async getSummary(workspaceId: string): Promise<GithubIntegrationSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(280);
      return mockSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<GithubIntegrationSummary>(`/workspaces/${workspaceId}/integrations/github`);
    return response.data;
  },

  async connect(workspaceId: string): Promise<GithubIntegrationSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(500);
      mockSummary = {
        ...mockSummary,
        connection: { ...mockSummary.connection, status: "connected", lastSyncedAt: "just now" },
      };
      return mockSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.post<GithubIntegrationSummary>(`/workspaces/${workspaceId}/integrations/github/oauth/start`);
    return response.data;
  },

  async sync(workspaceId: string): Promise<GithubIntegrationSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(650);
      mockSummary = {
        ...mockSummary,
        connection: { ...mockSummary.connection, status: "connected", lastSyncedAt: "just now" },
        repositories: mockSummary.repositories.map((repo, index) => ({ ...repo, commitsToday: repo.commitsToday + (index === 0 ? 1 : 0) })),
      };
      return mockSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.post<GithubIntegrationSummary>(`/workspaces/${workspaceId}/integrations/github/sync`);
    return response.data;
  },
};


