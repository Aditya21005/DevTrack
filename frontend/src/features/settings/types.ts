export type WorkspaceVisibility = "private" | "organization";
export type MemberRole = "owner" | "admin" | "member" | "viewer";
export type MemberStatus = "active" | "invited" | "suspended";

export interface WorkspaceSettings {
  id: string;
  name: string;
  slug: string;
  defaultTimezone: string;
  visibility: WorkspaceVisibility;
  aiEnabled: boolean;
  githubRequired: boolean;
}

export interface WorkspaceMember {
  id: string;
  name: string;
  email: string;
  initials: string;
  role: MemberRole;
  status: MemberStatus;
  lastActiveAt: string;
}

export interface AuditEvent {
  id: string;
  actor: string;
  action: string;
  resource: string;
  createdAt: string;
}

export interface SettingsSummary {
  workspace: WorkspaceSettings;
  members: WorkspaceMember[];
  auditEvents: AuditEvent[];
}

export interface WorkspaceSettingsInput {
  name: string;
  slug: string;
  defaultTimezone: string;
  visibility: WorkspaceVisibility;
  aiEnabled: boolean;
  githubRequired: boolean;
}

export interface InviteMemberInput {
  email: string;
  role: MemberRole;
}