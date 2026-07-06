import { useState } from "react";
import { Bot, BrainCircuit, FileCheck2, RefreshCcw, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AiActivityRail } from "../components/AiActivityRail";
import { AiArtifactPanel } from "../components/AiArtifactPanel";
import { AiModeSelector } from "../components/AiModeSelector";
import { PromptComposer } from "../components/PromptComposer";
import { useAiHistory } from "../hooks/useAiHistory";
import { useGenerateArtifact } from "../hooks/useGenerateArtifact";
import type { AiArtifact, AiMode, AiPromptInput } from "../types";

const workspaceId = "workspace_platform_engineering";

export default function AiWorkspacePage() {
  const [mode, setMode] = useState<AiMode>("task_breakdown");
  const [artifact, setArtifact] = useState<AiArtifact | null>(null);
  const historyQuery = useAiHistory(workspaceId);
  const generateArtifact = useGenerateArtifact(workspaceId);

  const submitPrompt = (input: AiPromptInput) => {
    generateArtifact.mutate(input, {
      onSuccess: setArtifact,
    });
  };

  return (
    <main className="space-y-6 p-5 sm:p-6 lg:p-8">
      <section className="relative overflow-hidden rounded-lg border border-border bg-card p-5 shadow-panel sm:p-6">
        <div className="absolute bottom-0 right-7 top-0 hidden w-16 branch-rail opacity-20 lg:block" aria-hidden="true" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-bold text-accent">
              <BrainCircuit className="size-4" />
              AI Workspace
            </div>
            <h1 className="mt-5 max-w-4xl font-display text-4xl font-bold leading-tight tracking-normal sm:text-5xl">
              Generate artifacts your engineering team can actually review.
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-foreground/62 sm:text-base">
              Task breakdowns, documentation drafts, sprint plans, and daily summaries shaped for DevTrack workflows.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 lg:min-w-[390px]">
            <div className="rounded-lg border border-border bg-background p-3">
              <Bot className="size-4 text-accent" />
              <p className="mt-2 text-2xl font-bold">4</p>
              <p className="text-xs font-semibold text-foreground/50">Modes</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <FileCheck2 className="size-4 text-success" />
              <p className="mt-2 text-2xl font-bold">{historyQuery.data?.filter((item) => item.accepted).length ?? 0}</p>
              <p className="text-xs font-semibold text-foreground/50">Accepted</p>
            </div>
            <div className="rounded-lg border border-border bg-background p-3">
              <Sparkles className="size-4 text-primary" />
              <p className="mt-2 text-2xl font-bold">{historyQuery.data?.length ?? 0}</p>
              <p className="text-xs font-semibold text-foreground/50">Artifacts</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[430px_1fr]">
        <aside className="space-y-5">
          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Generation Mode</h2>
            <p className="mt-1 text-sm text-foreground/58">Pick the output shape before writing the prompt.</p>
            <div className="mt-5">
              <AiModeSelector value={mode} onChange={setMode} />
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="font-display text-xl font-bold tracking-normal">Prompt</h2>
            <p className="mt-1 text-sm text-foreground/58">Keep assumptions explicit and give enough project context.</p>
            <div className="mt-5">
              <PromptComposer mode={mode} isGenerating={generateArtifact.isPending} onSubmit={submitPrompt} />
            </div>
            {generateArtifact.isError ? (
              <div className="mt-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm font-semibold text-warning">
                Generation failed. Try again or reduce the prompt scope.
              </div>
            ) : null}
          </Card>
        </aside>

        <section className="space-y-5">
          <AiArtifactPanel artifact={artifact} />
          <Card className="p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Prompt Engineering Guardrails</h2>
                <p className="mt-1 text-sm leading-6 text-foreground/58">
                  DevTrack prompts ask for structured, actionable output; avoid invented project facts; and surface assumptions as review material.
                </p>
              </div>
              <Button variant="secondary" type="button" onClick={() => historyQuery.refetch()} disabled={historyQuery.isFetching}>
                <RefreshCcw className="size-4" />
                Refresh history
              </Button>
            </div>
          </Card>
        </section>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <AiActivityRail items={historyQuery.data ?? []} />
        <Card className="p-5">
          <h2 className="font-display text-xl font-bold tracking-normal">Reusable Context Blocks</h2>
          <p className="mt-1 text-sm text-foreground/58">Copy these ideas into prompts when you need consistent outputs.</p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {["Acceptance criteria", "Dependency risks", "Reviewer checklist"].map((item, index) => (
              <div key={item} className="rounded-lg border border-border bg-background p-4">
                <span className="text-xs font-black text-accent">0{index + 1}</span>
                <p className="mt-3 text-sm font-bold">{item}</p>
                <p className="mt-2 text-xs leading-5 text-foreground/55">Use when the output should become project work, not just text.</p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </main>
  );
}