import { Github, GitPullRequestArrow, RadioTower } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { GithubSignal } from "../types";

interface GithubSyncCardProps {
  github: GithubSignal;
}

export function GithubSyncCard({ github }: GithubSyncCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">GitHub Sync</h2>
          <p className="mt-1 text-sm text-foreground/58">Metadata pipeline status.</p>
        </div>
        <div className="flex size-10 items-center justify-center rounded-md bg-foreground text-background">
          <Github className="size-5" />
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-3">
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-2xl font-bold">{github.repositories}</p>
          <p className="mt-1 text-xs font-semibold text-foreground/52">Repos</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-2xl font-bold">{github.pullRequests}</p>
          <p className="mt-1 text-xs font-semibold text-foreground/52">PRs</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-2xl font-bold">{github.commitsToday}</p>
          <p className="mt-1 text-xs font-semibold text-foreground/52">Commits</p>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between rounded-lg border border-success/25 bg-success/10 p-3 text-sm">
        <span className="inline-flex items-center gap-2 font-bold text-success"><RadioTower className="size-4" />{github.syncStatus}</span>
        <span className="inline-flex items-center gap-2 text-foreground/58"><GitPullRequestArrow className="size-4" />{github.lastSyncedAt}</span>
      </div>
    </Card>
  );
}