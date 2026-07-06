import { GitCommitHorizontal } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { GithubCommit } from "../types";

interface CommitFeedProps {
  commits: GithubCommit[];
}

export function CommitFeed({ commits }: CommitFeedProps) {
  return (
    <Card className="p-5">
      <h2 className="font-display text-xl font-bold tracking-normal">Commit Feed</h2>
      <p className="mt-1 text-sm text-foreground/58">Recent commits indexed into DevTrack.</p>
      <div className="mt-5 space-y-3">
        {commits.map((commit) => (
          <article key={commit.id} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-start gap-3">
              <GitCommitHorizontal className="mt-1 size-4 shrink-0 text-success" />
              <div className="min-w-0 flex-1">
                <p className="font-mono text-xs font-black text-primary">{commit.sha}</p>
                <h3 className="mt-2 text-sm font-bold leading-5">{commit.message}</h3>
                <p className="mt-1 text-xs text-foreground/52">{commit.repository} · {commit.author}</p>
              </div>
              <time className="shrink-0 text-xs font-semibold text-foreground/42">{commit.authoredAt}</time>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}