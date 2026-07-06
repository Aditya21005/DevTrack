export type GithubSyncStatus = "connected" | "syncing" | "attention" | "disconnected";
export type GithubIssueState = "open" | "closed";
export type GithubPullRequestState = "open" | "merged" | "closed" | "draft";

export interface GithubConnection {
  id: string;
  accountName: string;
  avatarUrl?: string;
  status: GithubSyncStatus;
  scopes: string[];
  lastSyncedAt: string;
}

export interface GithubRepository {
  id: string;
  name: string;
  fullName: string;
  visibility: "private" | "public";
  language: string;
  defaultBranch: string;
  openPullRequests: number;
  openIssues: number;
  commitsToday: number;
  linkedProjectKey?: string;
}

export interface GithubCommit {
  id: string;
  sha: string;
  message: string;
  author: string;
  repository: string;
  authoredAt: string;
}

export interface GithubIssue {
  id: string;
  number: number;
  title: string;
  state: GithubIssueState;
  labels: string[];
  repository: string;
  openedAt: string;
}

export interface GithubPullRequest {
  id: string;
  number: number;
  title: string;
  state: GithubPullRequestState;
  repository: string;
  author: string;
  targetBranch: string;
  openedAt: string;
}

export interface GithubIntegrationSummary {
  connection: GithubConnection;
  repositories: GithubRepository[];
  commits: GithubCommit[];
  issues: GithubIssue[];
  pullRequests: GithubPullRequest[];
}