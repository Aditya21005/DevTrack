import { GitBranch, LockKeyhole, RadioTower } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { GithubRepository } from "../types";

interface RepositoryListProps {
  repositories: GithubRepository[];
}

export function RepositoryList({ repositories }: RepositoryListProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border p-5">
        <h2 className="font-display text-xl font-bold tracking-normal">Repositories</h2>
        <p className="mt-1 text-sm text-foreground/58">Synced repository metadata and project links.</p>
      </div>
      <div className="divide-y divide-border">
        {repositories.map((repository) => (
          <article key={repository.id} className="grid gap-4 p-4 lg:grid-cols-[1fr_160px_170px] lg:items-center">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded bg-muted px-2 py-1 text-xs font-black text-foreground/62">
                  <LockKeyhole className="size-3" />
                  {repository.visibility}
                </span>
                {repository.linkedProjectKey ? <span className="rounded bg-primary/10 px-2 py-1 text-xs font-black text-primary">{repository.linkedProjectKey}</span> : null}
              </div>
              <h3 className="mt-3 truncate text-sm font-black">{repository.fullName}</h3>
              <p className="mt-1 text-xs font-semibold text-foreground/50">{repository.language} · default {repository.defaultBranch}</p>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs font-bold text-foreground/55 lg:text-left">
              <span>{repository.openPullRequests} PRs</span>
              <span>{repository.openIssues} issues</span>
              <span>{repository.commitsToday} commits</span>
            </div>
            <div className="flex items-center gap-2 text-sm font-semibold text-success">
              <RadioTower className="size-4" />
              Metadata healthy
              <GitBranch className="ml-auto size-4 text-foreground/35" />
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}