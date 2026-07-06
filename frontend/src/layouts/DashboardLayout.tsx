import { Bot, Gauge, Github, KanbanSquare, LogOut, Menu, Settings, SquareStack } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { useUiStore } from "@/store/ui.store";
import { useAuthStore } from "@/features/auth/store/auth.store";

const navItems = [
  { label: "Dashboard", href: "/app/dashboard", icon: Gauge },
  { label: "Projects", href: "/app/projects", icon: SquareStack },
  { label: "Kanban", href: "/app/projects/project_core_api/board", icon: KanbanSquare },
  { label: "AI", href: "/app/ai", icon: Bot },
  { label: "GitHub", href: "/app/integrations/github", icon: Github },
  { label: "Settings", href: "/app/settings", icon: Settings },
];

export function DashboardLayout() {
  const sidebarOpen = useUiStore((state) => state.sidebarOpen);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const clearSession = useAuthStore((state) => state.clearSession);
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();

  const logout = () => {
    clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-background text-foreground lg:grid lg:grid-cols-[auto_1fr]">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 -translate-x-full flex-col border-r border-border bg-card transition lg:sticky lg:translate-x-0",
          sidebarOpen && "translate-x-0",
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <div className="flex size-9 items-center justify-center rounded-md bg-primary text-white">
            <Gauge className="size-5" />
          </div>
          <div>
            <p className="font-display text-lg font-bold tracking-normal">DevTrack AI</p>
            <p className="text-xs font-semibold text-foreground/45">Engineering command</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-semibold text-foreground/62 transition hover:bg-muted hover:text-foreground",
                  isActive && "bg-primary/10 text-primary",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-4">
          <div className="rounded-lg bg-background p-3">
            <p className="text-sm font-bold">{user?.name ?? "Avery Chen"}</p>
            <p className="mt-1 truncate text-xs text-foreground/52">{user?.email ?? "avery@devtrack.ai"}</p>
          </div>
          <Button className="mt-3 w-full" variant="secondary" onClick={logout}>
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {sidebarOpen ? <button className="fixed inset-0 z-30 bg-foreground/20 lg:hidden" aria-label="Close navigation" onClick={toggleSidebar} /> : null}

      <div className="min-w-0">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/90 px-5 backdrop-blur sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Button className="lg:hidden" variant="secondary" onClick={toggleSidebar} aria-label="Open navigation">
              <Menu className="size-4" />
            </Button>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-foreground/42">Workspace</p>
              <p className="text-sm font-bold">Platform Engineering</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold text-success sm:flex">
            <span className="size-2 rounded-full bg-success" />
            Live mock data
          </div>
        </header>
        <Outlet />
      </div>
    </div>
  );
}