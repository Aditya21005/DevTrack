import { CircleDot, CircleOff } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { GithubIssue } from "../types";

interface IssueListProps {
  issues: GithubIssue[];
}

export function IssueList({ issues }: IssueListProps) {
  return (
    <Card className="p-5">
      <h2 className="font-display text-xl font-bold tracking-normal">Issues</h2>
      <p className="mt-1 text-sm text-foreground/58">GitHub issues available for project triage.</p>
      <div className="mt-5 space-y-3">
        {issues.map((issue) => (
          <article key={issue.id} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="text-xs font-black text-foreground/45">#{issue.number} · {issue.repository}</span>
                <h3 className="mt-2 text-sm font-bold leading-5">{issue.title}</h3>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {issue.labels.map((label) => <span key={label} className="rounded bg-muted px-2 py-1 text-[11px] font-bold text-foreground/55">{label}</span>)}
                </div>
              </div>
              <span className={issue.state === "open" ? "inline-flex items-center gap-1 rounded bg-success/10 px-2 py-1 text-xs font-black text-success" : "inline-flex items-center gap-1 rounded bg-muted px-2 py-1 text-xs font-black text-foreground/55"}>
                {issue.state === "open" ? <CircleDot className="size-3" /> : <CircleOff className="size-3" />}
                {issue.state}
              </span>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}