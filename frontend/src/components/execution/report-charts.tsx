"use client";

import * as React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CaseRail } from "@/components/execution/case-rail";
import {
  ChartContainer,
  ChartLegendContent,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  formatDurationMs,
  type CaseBucket,
  type ExecutionCase,
  type RunEvent,
  type RunSummary,
} from "@/lib/execution";

const STATUS_COLORS: Record<string, string> = {
  passed: "var(--severity-low)",
  failed: "var(--severity-critical)",
  skipped: "var(--severity-medium)",
  running: "var(--signal)",
  pending: "var(--severity-info)",
};

interface TimelinePoint {
  t: number;
  label: string;
  acked: number;
  nacked: number;
  ackRate: number;
  avgRtt: number | null;
}

export function buildTimeline(buckets: CaseBucket[], cases: ExecutionCase[]): TimelinePoint[] {
  const caseOrder = new Map(cases.map((c) => [c.test_case_id + ":" + c.position, c]));
  void caseOrder;
  const byCase = new Map<number, CaseBucket[]>();
  for (const bucket of buckets) {
    const list = byCase.get(bucket.position) ?? [];
    list.push(bucket);
    byCase.set(bucket.position, list);
  }
  const positions = [...byCase.keys()].sort((a, b) => a - b);
  const points: TimelinePoint[] = [];
  let cursor = 0;
  for (const position of positions) {
    const list = (byCase.get(position) ?? []).sort((a, b) => a.bucket_index - b.bucket_index);
    for (const bucket of list) {
      cursor += 1;
      const total = bucket.packets || 1;
      points.push({
        t: cursor,
        label: `#${position} · ${cursor}s`,
        acked: bucket.acked,
        nacked: bucket.nacked,
        ackRate: Math.round((100 * bucket.acked) / total),
        avgRtt: bucket.avg_rtt_ms,
      });
    }
  }
  return points;
}

export function OutcomeDonut({ summary }: { summary: RunSummary }) {
  const data = [
    { name: "Passed", value: summary.passed_cases, key: "passed" },
    { name: "Failed", value: summary.failed_cases, key: "failed" },
    { name: "Skipped", value: summary.by_status.skipped ?? 0, key: "skipped" },
  ].filter((d) => d.value > 0);
  if (data.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
        No completed cases yet
      </div>
    );
  }
  return (
    <ChartContainer config={{}} className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip content={<ChartTooltipContent />} />
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3} strokeWidth={0}>
            {data.map((entry) => (
              <Cell key={entry.key} fill={STATUS_COLORS[entry.key]} />
            ))}
          </Pie>
          <Legend content={<ChartLegendContent />} />
        </PieChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

export function DeliveryChart({ points }: { points: TimelinePoint[] }) {
  if (points.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
        Frame data appears as the run streams
      </div>
    );
  }
  return (
    <ChartContainer config={{}} className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={48} tick={{ fontSize: 11 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
          <Tooltip content={<ChartTooltipContent labelFormatter={(_, payload) => ((payload[0] as unknown as TimelinePoint | undefined)?.label ?? "")} />} />
          <Area type="monotone" dataKey="acked" name="ACK frames" stackId="1" fill="var(--severity-low)" stroke="var(--severity-low)" fillOpacity={0.25} />
          <Area type="monotone" dataKey="nacked" name="NACK frames" stackId="1" fill="var(--severity-critical)" stroke="var(--severity-critical)" fillOpacity={0.35} />
          <Legend content={<ChartLegendContent />} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

export function RttChart({ points }: { points: TimelinePoint[] }) {
  const data = points.filter((p) => p.avgRtt !== null);
  if (data.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
        RTT data appears as the run streams
      </div>
    );
  }
  return (
    <ChartContainer config={{}} className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={48} tick={{ fontSize: 11 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} unit=" ms" />
          <Tooltip content={<ChartTooltipContent />} />
          <Line type="monotone" dataKey="avgRtt" name="Avg RTT (ms)" stroke="var(--signal)" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

export function DurationChart({ cases }: { cases: ExecutionCase[] }) {
  const data = cases
    .filter((c) => c.duration_ms !== null)
    .map((c) => ({
      name: `#${c.position}`,
      full: c.test_case_name ?? `Case ${c.position}`,
      durationS: Math.round((c.duration_ms ?? 0) / 100) / 10,
      status: c.status,
    }));
  if (data.length === 0) {
    return (
      <div className="flex h-[240px] items-center justify-center text-sm text-muted-foreground">
        Durations appear when cases finish
      </div>
    );
  }
  return (
    <ChartContainer config={{}} className="h-[240px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
          <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} unit="s" />
          <Tooltip
            content={
              <ChartTooltipContent
                labelFormatter={(_, payload) => ((payload[0] as unknown as { full?: string } | undefined)?.full ?? "")}
                formatter={(value) => `${value} s`}
              />
            }
          />
          <Bar dataKey="durationS" name="Duration (s)" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={STATUS_COLORS[entry.status] ?? "var(--primary)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

export function EventsTimeline({ events }: { events: RunEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No events recorded yet.</p>;
  }
  return (
    <ScrollArea className="h-[240px]">
      <ol className="relative space-y-3 border-l border-border/70 py-1 pl-4 pr-3">
        {events.map((event, index) => (
          <li key={index} className="relative text-sm">
            <span className="absolute -left-[21px] top-1 size-2.5 rounded-full border-2 border-background bg-[var(--signal)]" />
            <div className="flex flex-wrap items-baseline gap-x-2">
              <span className="font-medium">{event.event_type.replace(/_/g, " ")}</span>
              <span className="font-tabular text-[11px] text-muted-foreground">
                {event.created_at ? new Date(event.created_at).toLocaleTimeString() : ""}
              </span>
            </div>
            {event.payload !== null && event.payload !== undefined && (
              <pre className="mt-1 overflow-x-auto rounded-md bg-muted/60 px-2 py-1 font-mono text-[11px] text-muted-foreground">
                {JSON.stringify(event.payload)}
              </pre>
            )}
          </li>
        ))}
      </ol>
    </ScrollArea>
  );
}

export function ReportCharts({
  summary,
  cases,
  buckets,
  events,
}: {
  summary: RunSummary;
  cases: ExecutionCase[];
  buckets: import("@/lib/execution").CaseBucket[];
  events: RunEvent[];
}) {
  const points = React.useMemo(() => buildTimeline(buckets, cases), [buckets, cases]);
  return (
    <div className="grid items-stretch gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Test cases run ({cases.length})</CardTitle>
          <CardDescription>Per-case outcome, attempts and delivery.</CardDescription>
        </CardHeader>
        <CardContent>
          <CaseRail cases={cases} activeCaseId={null} onSelect={() => {}} compact />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Outcome mix</CardTitle>
          <CardDescription>Share of passed, failed and skipped cases.</CardDescription>
        </CardHeader>
        <CardContent>
          <OutcomeDonut summary={summary} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Time per case</CardTitle>
          <CardDescription>
            Total {formatDurationMs(summary.total_duration_ms)} across {summary.total_cases} cases.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DurationChart cases={cases} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Frame delivery over time</CardTitle>
          <CardDescription>
            Acknowledged vs rejected ECU frames per second, in run order. NACK bursts mark fault windows.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DeliveryChart points={points} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Round-trip time over time</CardTitle>
          <CardDescription>Per-second mean ECU response latency. Fault windows show as latency spikes.</CardDescription>
        </CardHeader>
        <CardContent>
          <RttChart points={points} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Run timeline</CardTitle>
          <CardDescription>Audit trail of every state transition in this run.</CardDescription>
        </CardHeader>
        <CardContent>
          <EventsTimeline events={events} />
        </CardContent>
      </Card>
    </div>
  );
}
