import { GitCommitHorizontal } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { ProjectCommitSignal } from "../types";

interface ProjectCommitFeedProps {
  commits: ProjectCommitSignal[];
}

export function ProjectCommitFeed({ commits }: ProjectCommitFeedProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">Recent Commits</h2>
          <p className="mt-1 text-sm text-foreground/58">GitHub metadata synced into DevTrack.</p>
        </div>
        <GitCommitHorizontal className="size-5 text-success" />
      </div>
      <div className="mt-5 space-y-3">
        {commits.map((commit) => (
          <article key={commit.id} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-xs font-bold text-primary">{commit.sha}</p>
                <h3 className="mt-2 text-sm font-bold">{commit.message}</h3>
                <p className="mt-1 text-xs text-foreground/52">{commit.author}</p>
              </div>
              <time className="shrink-0 text-xs font-semibold text-foreground/42">{commit.time}</time>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}