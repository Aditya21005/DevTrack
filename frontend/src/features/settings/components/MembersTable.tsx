import { ShieldCheck, UserRound } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { WorkspaceMember } from "../types";

interface MembersTableProps {
  members: WorkspaceMember[];
}

export function MembersTable({ members }: MembersTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-border p-5">
        <h2 className="font-display text-xl font-bold tracking-normal">Members</h2>
        <p className="mt-1 text-sm text-foreground/58">Workspace access and role assignments.</p>
      </div>
      <div className="divide-y divide-border">
        {members.map((member) => (
          <article key={member.id} className="grid gap-3 p-4 sm:grid-cols-[1fr_120px_120px] sm:items-center">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-full bg-primary text-xs font-black text-white">{member.initials}</div>
              <div className="min-w-0">
                <h3 className="truncate text-sm font-bold">{member.name}</h3>
                <p className="truncate text-xs text-foreground/52">{member.email}</p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1 rounded bg-muted px-2 py-1 text-xs font-black capitalize text-foreground/62">
              <ShieldCheck className="size-3" />
              {member.role}
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-bold text-foreground/52">
              <UserRound className="size-3.5" />
              {member.status} · {member.lastActiveAt}
            </span>
          </article>
        ))}
      </div>
    </Card>
  );
}