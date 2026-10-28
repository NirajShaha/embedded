"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  Loader2,
  Pause,
  Play,
  Plug,
  Radio,
  Square,
  Terminal,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { listTestCases } from "@/lib/api";
import type { ExecutionCase, ExecutionRun } from "@/lib/execution";
import {
  DEFAULT_VECTOR_CONFIG,
  pauseCase,
  resumeCase,
  startCase,
  startTrace,
  stopCase,
  stopTrace,
  testConnection,
  type VectorConfig,
} from "@/lib/script-run";
import { useScriptStream, type FeedLine } from "@/hooks/use-script-stream";

interface ScriptRunDashboardProps {
  projectId: number;
  runId: number;
  initialCases: ExecutionCase[];
  initialRun: ExecutionRun;
  className?: string;
}

function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <Label className="text-[11px] text-muted-foreground">{label}</Label>
      <Input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="h-8"
      />
    </div>
  );
}

function ToggleField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="size-4 rounded border-border accent-primary"
      />
      {label}
    </label>
  );
}

function TerminalPanel({
  title,
  icon: Icon,
  lines,
  empty,
  renderLine,
  className,
  actions,
}: {
  title: string;
  icon: React.ElementType;
  lines: FeedLine[];
  empty: string;
  renderLine?: (line: FeedLine) => React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
}) {
  const scrollRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const node = scrollRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [lines]);

  return (
    <Card className={cn("flex min-h-0 flex-col overflow-hidden py-0", className)}>
      <CardHeader className="flex shrink-0 flex-row items-center justify-between gap-2 border-b border-border/60 px-3 py-2">
        <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Icon className="size-3.5" />
          {title}
          <span className="text-muted-foreground/50">· {lines.length}</span>
        </CardTitle>
        {actions}
      </CardHeader>
      <CardContent className="min-h-0 flex-1 overflow-hidden p-0">
        <div
          ref={scrollRef}
          className="h-full overflow-auto bg-[oklch(0.16_0.01_250)] p-3 font-mono text-[11px] leading-relaxed text-[oklch(0.9_0.02_150)]"
        >
          {lines.length === 0 ? (
            <span className="text-muted-foreground/70">{empty}</span>
          ) : (
            lines.map((line) => (
              <div key={line.id} className="whitespace-pre-wrap break-words">
                {renderLine ? renderLine(line) : line.line}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function ScriptRunDashboard({
  projectId,
  runId,
  initialCases,
  initialRun,
  className,
}: ScriptRunDashboardProps) {
  const stream = useScriptStream(runId);
  const cases = stream.cases.length > 0 ? stream.cases : initialCases;

  const [config, setConfig] = React.useState<VectorConfig>(DEFAULT_VECTOR_CONFIG);
  const [manualMessage, setManualMessage] = React.useState("");
  const [sourceId, setSourceId] = React.useState("");
  const [destinationId, setDestinationId] = React.useState("");
  const [selected, setSelected] = React.useState<Set<number>>(new Set());
  const [busy, setBusy] = React.useState<string | null>(null);
  const [connResult, setConnResult] = React.useState<{
    ok: boolean;
    message: string;
  } | null>(null);

  const patch = (changes: Partial<VectorConfig>) =>
    setConfig((prev) => ({ ...prev, ...changes }));

  // Map each test case to its category so we can group into tabs.
  const { data: catalog } = useQuery({
    queryKey: ["test-cases", projectId, "all"],
    queryFn: () => listTestCases(undefined, undefined, projectId),
  });

  const categoryByTestCase = React.useMemo(() => {
    const map = new Map<number, string>();
    for (const testCase of catalog ?? []) {
      map.set(testCase.id, testCase.category?.name ?? "Uncategorized");
    }
    return map;
  }, [catalog]);

  const categories = React.useMemo(() => {
    const set = new Set<string>();
    for (const runCase of cases) {
      set.add(categoryByTestCase.get(runCase.test_case_id) ?? "Uncategorized");
    }
    return Array.from(set);
  }, [cases, categoryByTestCase]);

  const [activeCategory, setActiveCategory] = React.useState<string | null>(null);
  // Fall back to the first category until the user picks one, without writing
  // state from an effect.
  const effectiveCategory =
    activeCategory ?? (categories.length > 0 ? categories[0] : null);

  const visibleCases = cases.filter(
    (runCase) =>
      (categoryByTestCase.get(runCase.test_case_id) ?? "Uncategorized") ===
      effectiveCategory,
  );

  const traceRunning = stream.traceState === "running";
  const traceActive = stream.traceState === "running" || stream.traceState === "paused";

  async function guard<T>(key: string, fn: () => Promise<T>): Promise<T | null> {
    setBusy(key);
    try {
      return await fn();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Action failed");
      return null;
    } finally {
      setBusy(null);
    }
  }

  const onTestConnection = () =>
    guard("test-conn", async () => {
      const result = await testConnection(runId, config);
      setConnResult(result);
      if (result.ok) toast.success("Connection OK");
      else toast.error("Connection failed");
    });

  const onStartTrace = () =>
    guard("trace-start", async () => {
      await startTrace(runId, config);
      toast.info("Trace window started");
    });

  const onStopTrace = () =>
    guard("trace-stop", async () => {
      await stopTrace(runId);
      toast.info("Trace window stopped");
    });

  const toggleSelected = (caseId: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(caseId)) next.delete(caseId);
      else next.add(caseId);
      return next;
    });

  const onStartCase = (runCase: ExecutionCase) =>
    guard(`case-${runCase.id}`, async () => {
      await startCase(runId, runCase.id, {
        config,
        sourceId,
        destinationId,
        manualMessage,
      });
      toast.success(`Started: ${runCase.test_case_name ?? `case ${runCase.id}`}`);
    });

  const onPauseCase = (runCase: ExecutionCase) =>
    guard(`case-${runCase.id}`, async () => {
      await pauseCase(runId, runCase.id);
    });

  const onResumeCase = (runCase: ExecutionCase) =>
    guard(`case-${runCase.id}`, async () => {
      await resumeCase(runId, runCase.id);
    });

  const onStopCase = (runCase: ExecutionCase) =>
    guard(`case-${runCase.id}-stop`, async () => {
      await stopCase(runId, runCase.id);
    });

  const caseLabel = (caseId: number | null) => {
    if (caseId === null) return null;
    const found = cases.find((c) => c.id === caseId);
    return found?.test_case_name ?? `Case ${caseId}`;
  };

  void initialRun;

  return (
    <div className={cn("flex min-h-0 flex-col gap-3 lg:flex-row", className)}>
      {/* LEFT: controls — one compact column that scrolls if needed */}
      <div className="flex min-h-0 flex-col gap-3 lg:w-[360px] lg:shrink-0 lg:overflow-y-auto lg:pr-1">
        {/* Vector config + trace + test connection */}
        <Card className="shrink-0 gap-0 py-0">
          <CardHeader className="flex flex-row items-center justify-between gap-2 border-b border-border/60 px-4 py-2.5">
            <CardTitle className="text-sm">Vector Config</CardTitle>
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span
                className={cn(
                  "size-2 rounded-full",
                  traceRunning
                    ? "bg-emerald-500"
                    : stream.traceState === "paused"
                      ? "bg-amber-500"
                      : "bg-muted-foreground/40",
                )}
              />
              Trace {stream.traceState ?? "idle"}
            </span>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 p-4">
            <div className="grid grid-cols-2 gap-2.5">
              <LabeledInput
                label="Interface"
                value={config.interface}
                onChange={(v) => patch({ interface: v })}
              />
              <LabeledInput
                label="Channel"
                type="number"
                value={config.channel}
                onChange={(v) => patch({ channel: Number(v) || 0 })}
              />
              <LabeledInput
                label="App name"
                value={config.app_name}
                onChange={(v) => patch({ app_name: v })}
              />
              <LabeledInput
                label="Bitrate"
                type="number"
                value={config.bitrate}
                onChange={(v) => patch({ bitrate: Number(v) || 0 })}
              />
              <LabeledInput
                label="Data bitrate"
                type="number"
                value={config.dbitrate}
                onChange={(v) => patch({ dbitrate: Number(v) || 0 })}
              />
              <div className="flex flex-col justify-end gap-1.5 pb-1">
                <ToggleField
                  label="FD"
                  checked={config.fd}
                  onChange={(v) => patch({ fd: v })}
                />
                <ToggleField
                  label="Receive own msgs"
                  checked={config.receive_own_messages}
                  onChange={(v) => patch({ receive_own_messages: v })}
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t border-border/60 pt-3">
              <Button
                size="sm"
                onClick={onStartTrace}
                disabled={busy !== null || traceRunning}
                className="gap-1.5"
              >
                {busy === "trace-start" ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Play className="size-3.5" />
                )}
                Start trace
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onStopTrace}
                disabled={busy !== null || !traceActive}
                className="gap-1.5"
              >
                <Square className="size-3.5" />
                Stop
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={onTestConnection}
                disabled={busy !== null}
                className="gap-1.5"
              >
                {busy === "test-conn" ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Plug className="size-3.5" />
                )}
                Test
              </Button>
              {connResult && (
                <span
                  className={cn(
                    "flex items-center gap-1 truncate text-xs",
                    connResult.ok ? "text-emerald-600" : "text-destructive",
                  )}
                  title={connResult.message}
                >
                  {connResult.ok ? (
                    <CheckCircle2 className="size-3.5 shrink-0" />
                  ) : (
                    <XCircle className="size-3.5 shrink-0" />
                  )}
                  <span className="truncate">
                    {connResult.ok ? "Connected" : "Failed"}
                  </span>
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Manual message + IDs */}
        <Card className="shrink-0 py-0">
          <CardContent className="flex flex-col gap-2.5 p-4">
            <div className="flex flex-col gap-1">
              <Label className="text-[11px] text-muted-foreground">
                Msg to send
              </Label>
              <Textarea
                value={manualMessage}
                onChange={(event) => setManualMessage(event.target.value)}
                placeholder="02 10 03 00 00 00 00 00"
                className="h-14 resize-none font-mono text-xs"
              />
            </div>
            <div className="grid grid-cols-2 gap-2.5">
              <LabeledInput
                label="Source ID"
                value={sourceId}
                onChange={setSourceId}
                placeholder="0x400"
              />
              <LabeledInput
                label="Destination ID"
                value={destinationId}
                onChange={setDestinationId}
                placeholder="0x500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Category tabs + test cases */}
        <Card className="shrink-0 gap-0 py-0">
          <CardHeader className="border-b border-border/60 px-4 py-2.5">
            <CardTitle className="text-sm">Test cases</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2.5 p-4">
            {categories.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {categories.map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => setActiveCategory(category)}
                    className={cn(
                      "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                      effectiveCategory === category
                        ? "border-primary/40 bg-primary/10 text-foreground"
                        : "border-border bg-background text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {category}
                  </button>
                ))}
              </div>
            )}

            <div className="flex flex-col gap-2">
              {visibleCases.length === 0 ? (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  No test cases in this category.
                </p>
              ) : (
                visibleCases.map((runCase) => {
                  const proc = stream.caseStates[runCase.id];
                  const isRunning = proc?.state === "running";
                  const isPaused = proc?.state === "paused";
                  const isActive = isRunning || isPaused;
                  const isChecked = selected.has(runCase.id);
                  const rowBusy =
                    busy === `case-${runCase.id}` ||
                    busy === `case-${runCase.id}-stop`;

                  return (
                    <div
                      key={runCase.id}
                      className="flex items-center gap-2 rounded-lg border border-border/60 bg-card p-2"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleSelected(runCase.id)}
                        className="size-4 shrink-0 rounded border-border accent-primary"
                        aria-label={`Select ${runCase.test_case_name}`}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-medium">
                          {runCase.test_case_name ?? `Case ${runCase.id}`}
                        </p>
                        <StatusBadge status={runCase.status} proc={proc?.state} />
                      </div>

                      {isRunning ? (
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={() => onPauseCase(runCase)}
                          disabled={rowBusy}
                          className="gap-1"
                        >
                          <Pause className="size-3" />
                          Pause
                        </Button>
                      ) : (
                        <Button
                          size="xs"
                          onClick={() =>
                            isPaused ? onResumeCase(runCase) : onStartCase(runCase)
                          }
                          disabled={rowBusy || (!isActive && !isChecked)}
                          className="gap-1"
                        >
                          {rowBusy && !isActive ? (
                            <Loader2 className="size-3 animate-spin" />
                          ) : (
                            <Play className="size-3" />
                          )}
                          Start
                        </Button>
                      )}
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => onStopCase(runCase)}
                        disabled={rowBusy || !isActive}
                        className="gap-1"
                      >
                        <Square className="size-3" />
                        Stop
                      </Button>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* RIGHT: live feed + python terminal, filling the screen height */}
      <div className="flex min-h-0 flex-1 flex-col gap-3 max-lg:h-[560px]">
        <TerminalPanel
          className="flex-1"
          title="Live feed — trace window & test case scripts"
          icon={Radio}
          lines={stream.feed}
          empty="Start the trace or a test case to see live output here."
          actions={
            <span
              className={cn(
                "flex items-center gap-1 text-[11px]",
                stream.connected ? "text-emerald-600" : "text-muted-foreground",
              )}
            >
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  stream.connected ? "bg-emerald-500" : "bg-muted-foreground/40",
                )}
              />
              {stream.connected ? "live" : "offline"}
            </span>
          }
          renderLine={(line) => {
            const label =
              line.scope === "case" ? caseLabel(line.caseId) : "trace";
            return (
              <>
                <span className="text-[oklch(0.65_0.03_250)]">
                  [{label}]
                </span>{" "}
                {line.line}
              </>
            );
          }}
        />
        <TerminalPanel
          className="flex-1"
          title="Python terminal — script status"
          icon={Terminal}
          lines={stream.terminal}
          empty="Process status (started, paused, exited, errors) appears here."
        />
      </div>
    </div>
  );
}

function StatusBadge({
  status,
  proc,
}: {
  status: string;
  proc?: string;
}) {
  const label = proc ?? status;
  const tone =
    proc === "running" || status === "running"
      ? "bg-emerald-500/10 text-emerald-600"
      : proc === "paused"
        ? "bg-amber-500/10 text-amber-600"
        : status === "passed"
          ? "bg-emerald-500/10 text-emerald-600"
          : status === "failed"
            ? "bg-destructive/10 text-destructive"
            : "bg-muted text-muted-foreground";
  return (
    <Badge
      variant="secondary"
      className={cn("mt-0.5 h-4 px-1.5 text-[10px] font-normal", tone)}
    >
      {label}
    </Badge>
  );
}
