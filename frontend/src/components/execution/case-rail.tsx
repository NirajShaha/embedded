"use client";

import * as React from "react";
import {
  CheckCircle2,
  Circle,
  CircleDashed,
  Loader2,
  RotateCcw,
  SkipForward,
  XCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDurationMs, type ExecutionCase } from "@/lib/execution";

function caseTone(status: ExecutionCase["status"]): {
  dot: string;
  ring: string;
  badge: "default" | "secondary" | "destructive" | "outline";
  Icon: typeof Circle;
} {
  switch (status) {
    case "passed":
      return {
        dot: "bg-emerald-500",
        ring: "border-emerald-500/40 bg-emerald-500/5",
        badge: "default",
        Icon: CheckCircle2,
      };
    case "failed":
      return {
        dot: "bg-destructive",
        ring: "border-destructive/50 bg-destructive/5",
        badge: "destructive",
        Icon: XCircle,
      };
    case "running":
      return {
        dot: "bg-[var(--signal)]",
        ring: "border-[var(--signal)]/50 bg-[var(--signal)]/5",
        badge: "secondary",
        Icon: Loader2,
      };
    case "skipped":
      return {
        dot: "bg-amber-500",
        ring: "border-amber-500/30 bg-amber-500/5",
        badge: "outline",
        Icon: SkipForward,
      };
    default:
      return {
        dot: "bg-muted-foreground/40",
        ring: "border-border/60",
        badge: "outline",
        Icon: CircleDashed,
      };
  }
}

interface CaseRailProps {
  cases: ExecutionCase[];
  activeCaseId: number | null;
  onSelect: (caseId: number) => void;
  compact?: boolean;
}

export function CaseRail({ cases, activeCaseId, onSelect, compact }: CaseRailProps) {
  return (
    <ScrollArea className={cn(compact ? "h-[420px]" : "h-[560px]")}>
      <ol className="flex flex-col gap-2 pr-3">
        {cases.map((item) => {
          const tone = caseTone(item.status);
          const Icon = tone.Icon;
          const progress =
            item.packets_planned > 0
              ? Math.round((100 * item.packets_sent) / item.packets_planned)
              : 0;
          const selected = item.id === activeCaseId;
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(item.id)}
                className={cn(
                  "w-full rounded-lg border p-3 text-left transition-colors",
                  "hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60",
                  tone.ring,
                  selected && "ring-2 ring-ring/60",
                )}
              >
                <div className="flex items-start gap-2.5">
                  <span className={cn("mt-1.5 size-2 shrink-0 rounded-full", tone.dot)} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium text-muted-foreground">
                        #{item.position}
                      </span>
                      <Badge variant={tone.badge} className="gap-1 text-[10px]">
                        <Icon
                          className={cn(
                            "size-3",
                            item.status === "running" && "animate-spin",
                          )}
                        />
                        {item.status}
                        {item.attempt > 1 ? ` · try ${item.attempt}` : ""}
                      </Badge>
                    </div>
                    <p className="mt-1 line-clamp-2 text-sm font-medium leading-snug">
                      {item.test_case_name ?? `Test case ${item.test_case_id}`}
                    </p>
                    {(item.status === "running" || item.status === "passed" || item.status === "failed") && (
                      <div className="mt-2 space-y-1">
                        <Progress value={progress} className="h-1" />
                        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                          <span className="font-tabular">
                            {item.packets_sent}/{item.packets_planned} frames
                          </span>
                          <span className="font-tabular">
                            {formatDurationMs(item.duration_ms)}
                          </span>
                        </div>
                      </div>
                    )}
                    {item.status === "failed" && item.error && (
                      <p className="mt-1.5 line-clamp-2 text-xs text-destructive">
                        {item.error}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            </li>
          );
        })}
      </ol>
    </ScrollArea>
  );
}

export function CaseRailFallback() {
  return (
    <div className="flex h-[420px] items-center justify-center gap-2 text-sm text-muted-foreground">
      <Circle className="size-4 animate-pulse" />
      Waiting for run snapshot…
    </div>
  );
}

export { RotateCcw };
