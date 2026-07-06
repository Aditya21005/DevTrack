import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Github, LockKeyhole, Mail } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLogin } from "../hooks/useLogin";

const loginSchema = z.object({
  email: z.string().email("Enter a valid work email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const login = useLogin();
  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "avery@devtrack.ai",
      password: "devtrack-demo",
    },
  });

  const onSubmit = form.handleSubmit((values) => login.mutate(values));

  return (
    <form className="space-y-5" onSubmit={onSubmit} noValidate>
      <div className="space-y-2">
        <label className="text-sm font-semibold" htmlFor="email">
          Work email
        </label>
        <div className="relative">
          <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-foreground/45" />
          <Input id="email" type="email" className="pl-9" autoComplete="email" {...form.register("email")} />
        </div>
        {form.formState.errors.email ? <p className="text-sm text-warning">{form.formState.errors.email.message}</p> : null}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-semibold" htmlFor="password">
          Password
        </label>
        <div className="relative">
          <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-foreground/45" />
          <Input id="password" type="password" className="pl-9" autoComplete="current-password" {...form.register("password")} />
        </div>
        {form.formState.errors.password ? <p className="text-sm text-warning">{form.formState.errors.password.message}</p> : null}
      </div>

      {login.isError ? (
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-foreground">
          We could not start your session. Check your credentials and try again.
        </div>
      ) : null}

      <Button className="w-full" type="submit" disabled={login.isPending}>
        {login.isPending ? "Opening workspace" : "Open DevTrack"}
        <ArrowRight className="size-4" />
      </Button>

      <Button className="w-full" type="button" variant="secondary">
        <Github className="size-4" />
        Continue with GitHub
      </Button>
    </form>
  );
}
