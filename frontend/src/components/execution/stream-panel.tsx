"use client";

import * as React from "react";
import { ArrowDownToLine, Pause, Radio } from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  formatClock,
  useNow,
  type ExecutionCase,
  type PacketFrame,
} from "@/lib/execution";

interface StreamPanelProps {
  packets: PacketFrame[];
  cases: ExecutionCase[];
  connected: boolean;
  activeCaseId: number | null;
}

function hexGroups(hex: string): string[] {
  const groups: string[] = [];
  for (let i = 0; i < hex.length; i += 2) groups.push(hex.slice(i, i + 2));
  return groups.slice(0, 16);
}

export function StreamPanel({ packets, cases, connected, activeCaseId }: StreamPanelProps) {
  const [pinned, setPinned] = React.useState(true);
  const [filter, setFilter] = React.useState<"all" | "acked" | "nacked">("all");
  const viewportRef = React.useRef<HTMLDivElement>(null);

  const byId = React.useMemo(() => new Map(cases.map((c) => [c.id, c])), [cases]);
  const activeCase = activeCaseId !== null ? byId.get(activeCaseId) : undefined;
  const ticking = activeCase?.status === "running" && activeCase.started_at !== null;
  const now = useNow(ticking, 1000);

  // eslint-disable-next-line react-hooks/preserve-manual-memoization
  const elapsed = React.useMemo(() => {
    if (!activeCase?.started_at) return "—";
    const start = new Date(activeCase.started_at).getTime();
    const end = activeCase.finished_at ? new Date(activeCase.finished_at).getTime() : now;
    if (Number.isNaN(start)) return "—";
    return `${Math.max(0, Math.round((end - start) / 1000))}s`;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCase, now]);
  const visible = React.useMemo(() => {
    let rows = packets;
    if (activeCaseId !== null) rows = rows.filter((p) => p.case_id === activeCaseId);
    if (filter === "acked") rows = rows.filter((p) => p.ack);
    if (filter === "nacked") rows = rows.filter((p) => !p.ack);
    return rows.slice(-250);
  }, [packets, activeCaseId, filter]);

  React.useEffect(() => {
    if (!pinned) return;
    const el = viewportRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [visible.length, pinned]);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between gap-3 border-b pb-3">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm">Binary packet stream</CardTitle>
          <Badge variant={connected ? "default" : "destructive"} className="gap-1.5 text-[10px]">
            <span className={cn("size-1.5 rounded-full", connected ? "bg-emerald-300 animate-pulse" : "bg-current")} />
            {connected ? "live" : "reconnecting"}
          </Badge>
        </div>
        <div className="flex items-center gap-1.5">
          {(["all", "acked", "nacked"] as const).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setFilter(key)}
              className={cn(
                "rounded-md px-2 py-1 text-[11px] font-medium transition-colors",
                filter === key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {key === "all" ? "All" : key === "acked" ? "ACK" : "NACK"}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setPinned((v) => !v)}
            title={pinned ? "Pause auto-scroll" : "Resume auto-scroll"}
            className={cn(
              "ml-1 inline-flex size-7 items-center justify-center rounded-md transition-colors",
              pinned ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted",
            )}
          >
            {pinned ? <Pause className="size-3.5" /> : <ArrowDownToLine className="size-3.5" />}
          </button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {activeCase && (
          <div className="grid grid-cols-2 gap-px border-b bg-border/60 text-xs sm:grid-cols-4">
            {[
              ["Start", formatClock(activeCase.started_at)],
              ["End", activeCase.finished_at ? formatClock(activeCase.finished_at) : activeCase.status === "running" ? "streaming…" : "—"],
              ["Elapsed", elapsed],
              [
                "Delivery",
                activeCase.packets_sent > 0
                  ? `${Math.round((100 * activeCase.packets_acked) / activeCase.packets_sent)}% ACK`
                  : "—",
              ],
            ].map(([label, value]) => (
              <div key={label} className="bg-card px-3 py-2">
                <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{label}</div>
                <div className="font-tabular font-medium">{value}</div>
              </div>
            ))}
          </div>
        )}
        <ScrollArea className="h-[480px]">
          <div ref={viewportRef} className="h-[480px] overflow-y-auto px-3 py-2 font-mono text-[11px] leading-relaxed">
            {visible.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
                <Radio className="size-5 animate-pulse" />
                <p className="font-sans text-xs">Waiting for frames…</p>
              </div>
            ) : (
              visible.map((packet, index) => (
                <div
                  key={`${packet.case_id}-${packet.seq}-${index}`}
                  className={cn(
                    "flex items-baseline gap-2 rounded px-1.5 py-0.5",
                    !packet.ack && "bg-destructive/10 text-destructive",
                  )}
                >
                  <span className="w-14 shrink-0 text-muted-foreground">#{packet.seq}</span>
                  <span className="flex flex-1 flex-wrap gap-x-1 break-all">
                    {hexGroups(packet.payload_hex).map((byte, i) => (
                      <span key={i} className={cn(!packet.ack && i % 2 === 0 && "font-bold")}>
                        {byte}
                      </span>
                    ))}
                  </span>
                  <span className={cn("shrink-0 font-sans text-[10px] font-semibold", packet.ack ? "text-emerald-600 dark:text-emerald-400" : "text-destructive")}>
                    {packet.ack ? "ACK" : "NACK"}
                  </span>
                  <span className="hidden w-16 shrink-0 text-right text-muted-foreground sm:inline">
                    {packet.rtt_ms.toFixed(1)} ms
                  </span>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
