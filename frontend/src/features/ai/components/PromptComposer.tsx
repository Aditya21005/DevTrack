import { zodResolver } from "@hookform/resolvers/zod";
import { SendHorizontal } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AiMode, AiPromptInput } from "../types";

const promptSchema = z.object({
  mode: z.enum(["task_breakdown", "documentation", "sprint_planning", "daily_summary"]),
  projectContext: z.string().min(3, "Add a project or workflow context"),
  prompt: z.string().min(12, "Give the assistant a little more context"),
});

interface PromptComposerProps {
  mode: AiMode;
  isGenerating: boolean;
  onSubmit: (input: AiPromptInput) => void;
}

export function PromptComposer({ mode, isGenerating, onSubmit }: PromptComposerProps) {
  const form = useForm<AiPromptInput>({
    resolver: zodResolver(promptSchema),
    defaultValues: {
      mode,
      projectContext: "Core API Reliability",
      prompt: "Break down the remaining release hardening work and call out review risks.",
    },
  });

  useEffect(() => {
    form.setValue("mode", mode);
  }, [form, mode]);

  return (
    <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
      <input type="hidden" {...form.register("mode")} />
      <div className="space-y-1.5">
        <label className="text-xs font-bold text-foreground/60" htmlFor="project-context">Project context</label>
        <Input id="project-context" {...form.register("projectContext")} />
        {form.formState.errors.projectContext ? <p className="text-xs text-warning">{form.formState.errors.projectContext.message}</p> : null}
      </div>

      <div className="space-y-1.5">
        <label className="text-xs font-bold text-foreground/60" htmlFor="ai-prompt">Prompt</label>
        <textarea
          id="ai-prompt"
          className="min-h-40 w-full resize-y rounded-md border border-border bg-background px-3 py-3 text-sm leading-6 text-foreground shadow-sm transition placeholder:text-foreground/40 focus-visible:ring-2 focus-visible:ring-ring"
          {...form.register("prompt")}
        />
        {form.formState.errors.prompt ? <p className="text-xs text-warning">{form.formState.errors.prompt.message}</p> : null}
      </div>

      <Button className="w-full" type="submit" disabled={isGenerating}>
        <SendHorizontal className="size-4" />
        {isGenerating ? "Generating artifact" : "Generate artifact"}
      </Button>
    </form>
  );
}