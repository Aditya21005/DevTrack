import { Activity, Bot, GitBranch, ShieldCheck } from "lucide-react";

import { Card } from "@/components/ui/card";
import { LoginForm } from "../components/LoginForm";

const signals = [
  { label: "AI task breakdowns", icon: Bot },
  { label: "GitHub sync", icon: GitBranch },
  { label: "Delivery health", icon: Activity },
  { label: "Workspace controls", icon: ShieldCheck },
];

export default function LoginPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="relative hidden border-r border-border bg-card px-10 py-10 lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-y-12 left-10 w-14 branch-rail opacity-80" aria-hidden="true" />
          <div className="relative ml-20">
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-semibold">
              <span className="size-2 rounded-full bg-success" />
              DevTrack AI
            </div>
            <h1 className="mt-12 max-w-2xl font-display text-5xl font-bold leading-tight tracking-normal">
              Plan work, read code signals, and let AI turn intent into tasks.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-foreground/68">
              A command center for engineering teams that need project tracking, GitHub visibility, and focused AI assistance in one workflow.
            </p>
          </div>

          <div className="relative ml-20 grid max-w-2xl grid-cols-2 gap-3">
            {signals.map((signal) => (
              <div key={signal.label} className="rounded-lg border border-border bg-background p-4">
                <signal.icon className="size-5 text-primary" />
                <p className="mt-3 text-sm font-semibold">{signal.label}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="flex items-center justify-center px-5 py-8 sm:px-8">
          <div className="w-full max-w-md animate-[fade-in_220ms_ease-out]">
            <div className="mb-8 lg:hidden">
              <div className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold">
                <span className="size-2 rounded-full bg-success" />
                DevTrack AI
              </div>
            </div>

            <Card className="p-6 sm:p-8">
              <div className="mb-7">
                <p className="text-sm font-semibold text-primary">Secure workspace login</p>
                <h2 className="mt-2 font-display text-3xl font-bold tracking-normal">Welcome back</h2>
                <p className="mt-2 text-sm leading-6 text-foreground/60">
                  Use the demo credentials or connect your real backend by setting VITE_USE_MOCK_API=false.
                </p>
              </div>
              <LoginForm />
            </Card>

            <p className="mt-6 text-center text-sm text-foreground/55">
              Protected by workspace roles, short-lived tokens, and audit-ready sessions.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
