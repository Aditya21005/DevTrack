import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateProject } from "../hooks/useCreateProject";
import type { CreateProjectInput, ProjectPriority } from "../types";

const createProjectSchema = z.object({
  key: z.string().min(2, "Use at least 2 characters").max(8, "Keep keys short").regex(/^[a-zA-Z0-9]+$/, "Letters and numbers only"),
  name: z.string().min(3, "Name is required"),
  description: z.string().min(10, "Add a short project description"),
  priority: z.enum(["low", "medium", "high", "urgent"]),
  dueDate: z.string().min(1, "Deadline is required"),
});

interface CreateProjectFormProps {
  workspaceId: string;
}

export function CreateProjectForm({ workspaceId }: CreateProjectFormProps) {
  const createProject = useCreateProject(workspaceId);
  const form = useForm<CreateProjectInput>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: {
      key: "OPS",
      name: "Operational Readiness",
      description: "Prepare launch controls, audit checks, and release health reviews.",
      priority: "medium",
      dueDate: "2026-07-30",
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    createProject.mutate(values, {
      onSuccess: () => {
        form.reset({ key: "", name: "", description: "", priority: "medium", dueDate: "" });
      },
    });
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit} noValidate>
      <div className="grid gap-3 sm:grid-cols-[110px_1fr]">
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="project-key">Key</label>
          <Input id="project-key" maxLength={8} {...form.register("key")} />
          {form.formState.errors.key ? <p className="text-xs text-warning">{form.formState.errors.key.message}</p> : null}
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="project-name">Project name</label>
          <Input id="project-name" {...form.register("name")} />
          {form.formState.errors.name ? <p className="text-xs text-warning">{form.formState.errors.name.message}</p> : null}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-xs font-bold text-foreground/60" htmlFor="project-description">Description</label>
        <Input id="project-description" {...form.register("description")} />
        {form.formState.errors.description ? <p className="text-xs text-warning">{form.formState.errors.description.message}</p> : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="project-priority">Priority</label>
          <select
            id="project-priority"
            className="h-11 w-full rounded-md border border-border bg-background px-3 text-sm font-semibold text-foreground shadow-sm transition focus-visible:ring-2 focus-visible:ring-ring"
            {...form.register("priority")}
          >
            {(["low", "medium", "high", "urgent"] satisfies ProjectPriority[]).map((priority) => (
              <option key={priority} value={priority}>{priority}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-foreground/60" htmlFor="project-due-date">Deadline</label>
          <Input id="project-due-date" type="date" {...form.register("dueDate")} />
          {form.formState.errors.dueDate ? <p className="text-xs text-warning">{form.formState.errors.dueDate.message}</p> : null}
        </div>
      </div>

      {createProject.isError ? <p className="text-sm text-warning">Project could not be created. Try again.</p> : null}

      <Button className="w-full" type="submit" disabled={createProject.isPending}>
        <Plus className="size-4" />
        {createProject.isPending ? "Creating project" : "Create project"}
      </Button>
    </form>
  );
}