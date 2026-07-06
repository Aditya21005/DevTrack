import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { ProjectFilters as ProjectFiltersValue, ProjectStatus } from "../types";

const statusOptions: Array<{ label: string; value: ProjectStatus | "all" }> = [
  { label: "All statuses", value: "all" },
  { label: "Planned", value: "planned" },
  { label: "Active", value: "active" },
  { label: "At risk", value: "at_risk" },
  { label: "On hold", value: "on_hold" },
  { label: "Completed", value: "completed" },
];

interface ProjectFiltersProps {
  value: ProjectFiltersValue;
  onChange: (filters: ProjectFiltersValue) => void;
}

export function ProjectFilters({ value, onChange }: ProjectFiltersProps) {
  return (
    <div className="grid gap-3 md:grid-cols-[1fr_220px]">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-foreground/42" />
        <Input
          className="pl-9"
          placeholder="Search projects, keys, repositories"
          value={value.search ?? ""}
          onChange={(event) => onChange({ ...value, search: event.target.value })}
        />
      </div>
      <select
        className="h-11 rounded-md border border-border bg-background px-3 text-sm font-semibold text-foreground shadow-sm transition focus-visible:ring-2 focus-visible:ring-ring"
        value={value.status ?? "all"}
        onChange={(event) => onChange({ ...value, status: event.target.value as ProjectStatus | "all" })}
      >
        {statusOptions.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </div>
  );
}