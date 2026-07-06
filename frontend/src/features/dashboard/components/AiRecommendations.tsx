import { Bot, Sparkles } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { AiRecommendation } from "../types";

interface AiRecommendationsProps {
  recommendations: AiRecommendation[];
}

export function AiRecommendations({ recommendations }: AiRecommendationsProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-bold tracking-normal">AI Recommendations</h2>
          <p className="mt-1 text-sm text-foreground/58">Practical next moves based on delivery signals.</p>
        </div>
        <div className="flex size-10 items-center justify-center rounded-md bg-accent/10 text-accent">
          <Bot className="size-5" />
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {recommendations.map((recommendation) => (
          <article key={recommendation.id} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-sm font-bold">
                  <Sparkles className="size-4 text-accent" />
                  {recommendation.title}
                </div>
                <p className="mt-2 text-sm leading-6 text-foreground/60">{recommendation.detail}</p>
              </div>
              <span className="rounded bg-accent/10 px-2 py-1 text-xs font-bold text-accent">{recommendation.confidence}%</span>
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}