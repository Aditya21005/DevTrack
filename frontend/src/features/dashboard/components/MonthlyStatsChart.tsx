import { Card } from "@/components/ui/card";
import type { MonthlyStat } from "../types";

interface MonthlyStatsChartProps {
  stats: MonthlyStat[];
}

export function MonthlyStatsChart({ stats }: MonthlyStatsChartProps) {
  const maxValue = Math.max(...stats.flatMap((item) => [item.completed, item.pending]));

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">Monthly Flow</h2>
          <p className="mt-1 text-sm text-foreground/58">Completed versus pending work.</p>
        </div>
        <div className="flex gap-4 text-xs font-bold text-foreground/55">
          <span className="inline-flex items-center gap-2"><span className="size-2 rounded-full bg-success" />Completed</span>
          <span className="inline-flex items-center gap-2"><span className="size-2 rounded-full bg-warning" />Pending</span>
        </div>
      </div>

      <div className="mt-7 grid h-56 grid-cols-6 items-end gap-3 sm:gap-5">
        {stats.map((item) => (
          <div key={item.month} className="flex h-full flex-col justify-end gap-2">
            <div className="flex flex-1 items-end gap-1.5">
              <div className="w-full rounded-t bg-success/85" style={{ height: `${(item.completed / maxValue) * 100}%` }} />
              <div className="w-full rounded-t bg-warning/85" style={{ height: `${(item.pending / maxValue) * 100}%` }} />
            </div>
            <span className="text-center text-xs font-bold text-foreground/55">{item.month}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}