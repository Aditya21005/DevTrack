import { ArrowUpRight, Bot, CheckCircle2, Clock3, Gauge } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";
import type { DashboardMetric } from "../types";

const toneClasses = {
  primary: "text-primary bg-primary/10",
  success: "text-success bg-success/10",
  warning: "text-warning bg-warning/10",
  accent: "text-accent bg-accent/10",
};

const icons = {
  velocity: Gauge,
  completed: CheckCircle2,
  pending: Clock3,
  ai: Bot,
};

interface StatCardProps {
  metric: DashboardMetric;
}

export function StatCard({ metric }: StatCardProps) {
  const Icon = icons[metric.id as keyof typeof icons] ?? Gauge;

  return (
    <Card className="p-5 transition hover:-translate-y-0.5 hover:border-primary/35">
      <div className="flex items-start justify-between gap-3">
        <div className={cn("flex size-10 items-center justify-center rounded-md", toneClasses[metric.tone])}>
          <Icon className="size-5" />
        </div>
        <ArrowUpRight className="size-4 text-foreground/35" />
      </div>
      <p className="mt-5 text-sm font-medium text-foreground/58">{metric.label}</p>
      <div className="mt-1 flex items-end justify-between gap-3">
        <p className="font-display text-3xl font-bold tracking-normal">{metric.value}</p>
        <p className="pb-1 text-right text-xs font-semibold text-foreground/55">{metric.delta}</p>
      </div>
    </Card>
  );
}