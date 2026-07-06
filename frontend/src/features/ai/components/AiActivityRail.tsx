import { CheckCircle2, Clock3 } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { AiActivityItem } from "../types";

interface AiActivityRailProps {
  items: AiActivityItem[];
}

export function AiActivityRail({ items }: AiActivityRailProps) {
  return (
    <Card className="p-5">
      <h2 className="font-display text-xl font-bold tracking-normal">AI Activity</h2>
      <p className="mt-1 text-sm text-foreground/58">Recent artifacts generated for this workspace.</p>
      <div className="relative mt-6 space-y-5 pl-8 before:absolute before:bottom-3 before:left-3 before:top-3 before:w-px before:bg-border">
        {items.map((item) => (
          <article key={item.id} className="relative">
            <span className="absolute -left-[26px] top-1 size-3 rounded-full bg-accent ring-4 ring-card" />
            <div className="rounded-lg border border-border bg-background p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="rounded bg-accent/10 px-2 py-1 text-xs font-black text-accent">{item.mode.replace("_", " ")}</span>
                  <h3 className="mt-3 text-sm font-bold">{item.title}</h3>
                </div>
                {item.accepted ? <CheckCircle2 className="size-4 shrink-0 text-success" /> : <Clock3 className="size-4 shrink-0 text-warning" />}
              </div>
              <p className="mt-2 text-xs font-semibold text-foreground/45">{item.createdAt}</p>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}