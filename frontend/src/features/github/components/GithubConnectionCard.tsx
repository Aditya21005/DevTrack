import { Github, KeyRound, RadioTower } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { GithubConnection } from "../types";

interface GithubConnectionCardProps {
  connection: GithubConnection;
  isConnecting: boolean;
  isSyncing: boolean;
  onConnect: () => void;
  onSync: () => void;
}

export function GithubConnectionCard({ connection, isConnecting, isSyncing, onConnect, onSync }: GithubConnectionCardProps) {
  return (
    <Card className="p-5">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex size-12 items-center justify-center rounded-md bg-foreground text-background">
            <Github className="size-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-display text-2xl font-bold tracking-normal">{connection.accountName}</h2>
              <span className="inline-flex items-center gap-1 rounded bg-success/10 px-2 py-1 text-xs font-black text-success">
                <RadioTower className="size-3.5" />
                {connection.status}
              </span>
            </div>
            <p className="mt-2 text-sm leading-6 text-foreground/58">Last synced {connection.lastSyncedAt}. OAuth scopes are stored encrypted on the backend.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {connection.scopes.map((scope) => (
                <span key={scope} className="inline-flex items-center gap-1 rounded bg-muted px-2 py-1 text-xs font-bold text-foreground/58">
                  <KeyRound className="size-3" />
                  {scope}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="secondary" onClick={onConnect} disabled={isConnecting}>
            <Github className="size-4" />
            {isConnecting ? "Connecting" : "Reconnect OAuth"}
          </Button>
          <Button type="button" onClick={onSync} disabled={isSyncing}>
            <RadioTower className="size-4" />
            {isSyncing ? "Syncing" : "Sync metadata"}
          </Button>
        </div>
      </div>
    </Card>
  );
}