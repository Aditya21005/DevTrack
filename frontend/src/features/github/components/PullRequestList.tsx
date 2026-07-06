import { GitPullRequestArrow } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { GithubPullRequest } from "../types";

const stateClass = {
  open: "bg-primary/10 text-primary",
  merged: "bg-success/10 text-success",
  closed: "bg-muted text-foreground/55",
  draft: "bg-warning/10 text-warning",
};

interface PullRequestListProps {
  pullRequests: GithubPullRequest[];
}

export function PullRequestList({ pullRequests }: PullRequestListProps) {
  return (
    <Card className="p-5">
      <h2 className="font-display text-xl font-bold tracking-normal">Pull Requests</h2>
      <p className="mt-1 text-sm text-foreground/58">Review state across linked repositories.</p>
      <div className="mt-5 space-y-3">
        {pullRequests.map((pullRequest) => (
          <article key={pullRequest.id} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-start gap-3">
              <GitPullRequestArrow className="mt-1 size-4 shrink-0 text-primary" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-black text-foreground/45">#{pullRequest.number} · {pullRequest.repository}</span>
                  <span className={`rounded px-2 py-1 text-xs font-black ${stateClass[pullRequest.state]}`}>{pullRequest.state}</span>
                </div>
                <h3 className="mt-2 text-sm font-bold leading-5">{pullRequest.title}</h3>
                <p className="mt-1 text-xs text-foreground/52">{pullRequest.author} into {pullRequest.targetBranch} · {pullRequest.openedAt}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}