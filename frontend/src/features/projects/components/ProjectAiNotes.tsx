import { Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { ProjectAiNote } from "../types";

interface ProjectAiNotesProps {
  notes: ProjectAiNote[];
}

export function ProjectAiNotes({ notes }: ProjectAiNotesProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-md bg-accent/10 text-accent">
          <Sparkles className="size-5" />
        </div>
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">AI Notes</h2>
          <p className="mt-1 text-sm text-foreground/58">Planning signals from project context.</p>
        </div>
      </div>
      <div className="mt-5 space-y-3">
        {notes.map((note) => (
          <article key={note.id} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold">{note.title}</h3>
                <p className="mt-2 text-sm leading-6 text-foreground/60">{note.detail}</p>
              </div>
              <span className="rounded bg-accent/10 px-2 py-1 text-xs font-bold text-accent">{note.confidence}%</span>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}