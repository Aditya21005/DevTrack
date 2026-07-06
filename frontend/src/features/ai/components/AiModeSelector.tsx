import { Bot, CalendarCheck, FileText, ListChecks } from "lucide-react";

import { cn } from "@/lib/cn";
import type { AiMode } from "../types";

const modes: Array<{ mode: AiMode; label: string; description: string; icon: typeof Bot }> = [
  { mode: "task_breakdown", label: "Task Breakdown", description: "Turn intent into scoped tasks", icon: ListChecks },
  { mode: "documentation", label: "Documentation", description: "Draft technical docs", icon: FileText },
  { mode: "sprint_planning", label: "Sprint Planning", description: "Sequence candidate work", icon: CalendarCheck },
  { mode: "daily_summary", label: "Daily Summary", description: "Summarize progress and blockers", icon: Bot },
];

interface AiModeSelectorProps {
  value: AiMode;
  onChange: (mode: AiMode) => void;
}

export function AiModeSelector({ value, onChange }: AiModeSelectorProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {modes.map((item) => (
        <button
          key={item.mode}
          type="button"
          className={cn(
            "rounded-lg border border-border bg-background p-4 text-left transition hover:-translate-y-0.5 hover:border-primary/45 focus-visible:ring-2 focus-visible:ring-ring",
            value === item.mode && "border-primary bg-primary/10 text-primary",
          )}
          onClick={() => onChange(item.mode)}
        >
          <item.icon className="size-5" />
          <p className="mt-3 text-sm font-black">{item.label}</p>
          <p className="mt-1 text-xs font-semibold text-foreground/52">{item.description}</p>
        </button>
      ))}
    </div>
  );
}