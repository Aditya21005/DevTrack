import { zodResolver } from "@hookform/resolvers/zod";
import { SendHorizontal } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useInviteMember } from "../hooks/useInviteMember";
import type { InviteMemberInput, MemberRole } from "../types";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  role: z.enum(["owner", "admin", "member", "viewer"]),
});

interface InviteMemberFormProps {
  workspaceId: string;
}

export function InviteMemberForm({ workspaceId }: InviteMemberFormProps) {
  const inviteMember = useInviteMember(workspaceId);
  const form = useForm<InviteMemberInput>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", role: "member" },
  });

  return (
    <form className="space-y-3" onSubmit={form.handleSubmit((values) => inviteMember.mutate(values, { onSuccess: () => form.reset({ email: "", role: "member" }) }))} noValidate>
      <div className="space-y-1.5">
        <label className="text-xs font-bold text-foreground/60" htmlFor="invite-email">Email</label>
        <Input id="invite-email" type="email" placeholder="teammate@company.com" {...form.register("email")} />
        {form.formState.errors.email ? <p className="text-xs text-warning">{form.formState.errors.email.message}</p> : null}
      </div>
      <div className="space-y-1.5">
        <label className="text-xs font-bold text-foreground/60" htmlFor="invite-role">Role</label>
        <select id="invite-role" className="h-11 w-full rounded-md border border-border bg-background px-3 text-sm font-semibold text-foreground shadow-sm focus-visible:ring-2 focus-visible:ring-ring" {...form.register("role")}>
          {(["admin", "member", "viewer"] satisfies MemberRole[]).map((role) => <option key={role} value={role}>{role}</option>)}
        </select>
      </div>
      <Button className="w-full" type="submit" disabled={inviteMember.isPending}>
        <SendHorizontal className="size-4" />
        {inviteMember.isPending ? "Sending invite" : "Send invite"}
      </Button>
      {inviteMember.isSuccess ? <p className="text-sm font-semibold text-success">Invite sent.</p> : null}
    </form>
  );
}