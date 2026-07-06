import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUpdateWorkspaceSettings } from "../hooks/useUpdateWorkspaceSettings";
import type { WorkspaceSettings, WorkspaceSettingsInput } from "../types";

const schema = z.object({
  name: z.string().min(3, "Workspace name is required"),
  slug: z.string().min(3, "Slug is required").regex(/^[a-z0-9-]+$/, "Use lowercase letters, numbers, and dashes"),
  defaultTimezone: z.string().min(2, "Timezone is required"),
  visibility: z.enum(["private", "organization"]),
  aiEnabled: z.boolean(),
  githubRequired: z.boolean(),
});

interface WorkspaceSettingsFormProps {
  workspaceId: string;
  workspace: WorkspaceSettings;
}

export function WorkspaceSettingsForm({ workspaceId, workspace }: WorkspaceSettingsFormProps) {
  const updateSettings = useUpdateWorkspaceSettings(workspaceId);
  const form = useForm<WorkspaceSettingsInput>({
    resolver: zodResolver(schema),
    defaultValues: workspace,
  });

  useEffect(() => {
    form.reset(workspace);
  }, [form, workspace]);

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit((values) => updateSettings.mutate(values))} noValidate>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="workspace-name">Workspace name</label>
          <Input id="workspace-name" {...form.register("name")} />
          {form.formState.errors.name ? <p className="text-xs text-warning">{form.formState.errors.name.message}</p> : null}
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="workspace-slug">Slug</label>
          <Input id="workspace-slug" {...form.register("slug")} />
          {form.formState.errors.slug ? <p className="text-xs text-warning">{form.formState.errors.slug.message}</p> : null}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="timezone">Default timezone</label>
          <Input id="timezone" {...form.register("defaultTimezone")} />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="visibility">Visibility</label>
          <select id="visibility" className="h-11 w-full rounded-md border border-border bg-background px-3 text-sm font-semibold text-foreground shadow-sm focus-visible:ring-2 focus-visible:ring-ring" {...form.register("visibility")}>
            <option value="private">Private</option>
            <option value="organization">Organization</option>
          </select>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background p-4 text-sm font-bold">
          AI features
          <input className="size-4 accent-primary" type="checkbox" {...form.register("aiEnabled")} />
        </label>
        <label className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background p-4 text-sm font-bold">
          Require GitHub link
          <input className="size-4 accent-primary" type="checkbox" {...form.register("githubRequired")} />
        </label>
      </div>

      {updateSettings.isError ? <p className="text-sm text-warning">Workspace settings could not be saved.</p> : null}
      {updateSettings.isSuccess ? <p className="text-sm font-semibold text-success">Workspace settings saved.</p> : null}

      <Button type="submit" disabled={updateSettings.isPending}>
        <Save className="size-4" />
        {updateSettings.isPending ? "Saving" : "Save settings"}
      </Button>
    </form>
  );
}