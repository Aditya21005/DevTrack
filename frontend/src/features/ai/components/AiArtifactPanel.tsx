import { Bot, CheckCircle2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { AiArtifact } from "../types";

interface AiArtifactPanelProps {
  artifact: AiArtifact | null;
}

export function AiArtifactPanel({ artifact }: AiArtifactPanelProps) {
  if (!artifact) {
    return (
      <Card className="flex min-h-[520px] items-center justify-center p-8 text-center">
        <div className="max-w-sm">
          <div className="mx-auto flex size-12 items-center justify-center rounded-md bg-accent/10 text-accent">
            <Bot className="size-6" />
          </div>
          <h2 className="mt-5 font-display text-2xl font-bold tracking-normal">Ready for a focused AI pass</h2>
          <p className="mt-2 text-sm leading-6 text-foreground/58">
            Choose a mode, describe the project context, and generate a reviewable artifact for your team.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded bg-accent/10 px-2 py-1 text-xs font-black text-accent">
            <Bot className="size-3.5" />
            {artifact.mode.replace("_", " ")}
          </div>
          <h2 className="mt-4 font-display text-2xl font-bold tracking-normal">{artifact.title}</h2>
          <p className="mt-2 text-sm leading-6 text-foreground/60">{artifact.summary}</p>
        </div>
        <span className="inline-flex shrink-0 items-center gap-2 rounded-md bg-success/10 px-3 py-2 text-sm font-bold text-success">
          <CheckCircle2 className="size-4" />
          {artifact.confidence}% confidence
        </span>
      </div>

      <div className="mt-5 space-y-4">
        {artifact.sections.map((section) => (
          <section key={section.title} className="rounded-lg border border-border bg-background p-4">
            <h3 className="text-sm font-black">{section.title}</h3>
            <ul className="mt-3 space-y-2">
              {section.items.map((item) => (
                <li key={item} className="flex gap-2 text-sm leading-6 text-foreground/64">
                  <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Card>
  );
}