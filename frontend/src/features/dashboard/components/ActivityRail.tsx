import { GitBranch } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { ActivitySignal } from "../types";

const dotClasses = {
  primary: "bg-primary",
  success: "bg-success",
  warning: "bg-warning",
  accent: "bg-accent",
};

interface ActivityRailProps {
  activity: ActivitySignal[];
}

export function ActivityRail({ activity }: ActivityRailProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">Branch Rail</h2>
          <p className="mt-1 text-sm text-foreground/58">Signals from work, code, and AI.</p>
        </div>
        <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
          <GitBranch className="size-5" />
        </div>
      </div>

      <div className="relative mt-6 space-y-5 pl-8 before:absolute before:bottom-3 before:left-3 before:top-3 before:w-px before:bg-border">
        {activity.map((item) => (
          <article key={item.id} className="relative">
            <span className={cn("absolute -left-[26px] top-1 size-3 rounded-full ring-4 ring-card", dotClasses[item.tone])} />
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold">{item.title}</h3>
                <p className="mt-1 text-sm leading-6 text-foreground/58">{item.detail}</p>
              </div>
              <time className="shrink-0 text-xs font-semibold text-foreground/42">{item.time}</time>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}