import { History } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { AuditEvent } from "../types";

interface AuditLogPanelProps {
  events: AuditEvent[];
}

export function AuditLogPanel({ events }: AuditLogPanelProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
          <History className="size-5" />
        </div>
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">Audit Trail</h2>
          <p className="mt-1 text-sm text-foreground/58">Recent security-relevant workspace events.</p>
        </div>
      </div>
      <div className="relative mt-6 space-y-5 pl-8 before:absolute before:bottom-3 before:left-3 before:top-3 before:w-px before:bg-border">
        {events.map((event) => (
          <article key={event.id} className="relative">
            <span className="absolute -left-[26px] top-1 size-3 rounded-full bg-primary ring-4 ring-card" />
            <div>
              <h3 className="text-sm font-bold">{event.actor} {event.action}</h3>
              <p className="mt-1 text-xs font-semibold text-foreground/50">{event.resource} · {event.createdAt}</p>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}