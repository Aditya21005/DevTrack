import { mockDelay } from "@/lib/mock-api";
import { runtimeConfig } from "@/lib/runtime-config";
import type { InviteMemberInput, SettingsSummary, WorkspaceMember, WorkspaceSettingsInput } from "../types";


let mockSummary: SettingsSummary = {
  workspace: {
    id: "workspace_platform_engineering",
    name: "Platform Engineering",
    slug: "platform-engineering",
    defaultTimezone: "Asia/Kolkata",
    visibility: "private",
    aiEnabled: true,
    githubRequired: true,
  },
  members: [
    { id: "u1", name: "Avery Chen", email: "avery@devtrack.ai", initials: "AC", role: "owner", status: "active", lastActiveAt: "now" },
    { id: "u2", name: "Mira Patel", email: "mira@devtrack.ai", initials: "MP", role: "admin", status: "active", lastActiveAt: "12 min ago" },
    { id: "u3", name: "Noah Kim", email: "noah@devtrack.ai", initials: "NK", role: "member", status: "active", lastActiveAt: "1 hr ago" },
    { id: "u4", name: "Sam Rivera", email: "sam@devtrack.ai", initials: "SR", role: "member", status: "invited", lastActiveAt: "pending" },
  ],
  auditEvents: [
    { id: "a1", actor: "Avery Chen", action: "updated workspace settings", resource: "Platform Engineering", createdAt: "18 min ago" },
    { id: "a2", actor: "Mira Patel", action: "synced GitHub integration", resource: "devtrack-ai", createdAt: "44 min ago" },
    { id: "a3", actor: "Noah Kim", action: "changed project role", resource: "Core API Reliability", createdAt: "2 hrs ago" },
  ],
};

function initialsFromEmail(email: string): string {
  return email.slice(0, 2).toUpperCase();
}

export const settingsService = {
  async getSummary(workspaceId: string): Promise<SettingsSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(240);
      return mockSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.get<SettingsSummary>(`/workspaces/${workspaceId}/settings`);
    return response.data;
  },

  async updateWorkspace(workspaceId: string, input: WorkspaceSettingsInput): Promise<SettingsSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(420);
      mockSummary = {
        ...mockSummary,
        workspace: { ...mockSummary.workspace, ...input },
        auditEvents: [
          { id: `audit_${Date.now()}`, actor: "Avery Chen", action: "updated workspace settings", resource: input.name, createdAt: "just now" },
          ...mockSummary.auditEvents,
        ],
      };
      return mockSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.patch<SettingsSummary>(`/workspaces/${workspaceId}/settings`, input);
    return response.data;
  },

  async inviteMember(workspaceId: string, input: InviteMemberInput): Promise<SettingsSummary> {
    if (runtimeConfig.useMockApi) {
      await mockDelay(420);
      const member: WorkspaceMember = {
        id: `member_${Date.now()}`,
        name: input.email.split("@")[0],
        email: input.email,
        initials: initialsFromEmail(input.email),
        role: input.role,
        status: "invited",
        lastActiveAt: "pending",
      };
      mockSummary = {
        ...mockSummary,
        members: [member, ...mockSummary.members],
        auditEvents: [
          { id: `audit_${Date.now()}`, actor: "Avery Chen", action: "invited workspace member", resource: input.email, createdAt: "just now" },
          ...mockSummary.auditEvents,
        ],
      };
      return mockSummary;
    }

    const { apiClient } = await import("@/lib/api-client");
    const response = await apiClient.post<SettingsSummary>(`/workspaces/${workspaceId}/members/invite`, input);
    return response.data;
  },
};


