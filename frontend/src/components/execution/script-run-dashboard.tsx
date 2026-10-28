"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  Loader2,
  Maximize2,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

type SectionKind = "config" | "message" | "cases" | "feed" | "terminal";

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
    <div className="flex flex-col gap-0.5">
      <Label className="text-[10px] text-muted-foreground">{label}</Label>
      <Input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="h-7"
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

function MaximizeButton({
  onClick,
  label,
}: {
  onClick: () => void;
  label: string;
}) {
  return (
    <Button
      type="button"
      size="icon-xs"
      variant="ghost"
      className="text-muted-foreground hover:text-foreground"
      onClick={onClick}
      aria-label={`Maximize ${label}`}
      title="Maximize"
    >
      <Maximize2 className="size-3.5" />
    </Button>
  );
}

/** A card section with a title, optional header extras, and a maximize button. */
function Section({
  title,
  icon: Icon,
  onMaximize,
  headerExtra,
  children,
  className,
  bodyClassName,
}: {
  title: string;
  icon?: React.ElementType;
  onMaximize: () => void;
  headerExtra?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <Card className={cn("flex min-h-0 flex-col gap-0 overflow-hidden py-0", className)}>
      <CardHeader className="flex shrink-0 flex-row items-center justify-between gap-2 border-b border-border/60 px-3 py-1.5">
        <CardTitle className="flex items-center gap-2 text-[13px]">
          {Icon ? <Icon className="size-3.5 text-muted-foreground" /> : null}
          {title}
        </CardTitle>
        <div className="flex items-center gap-1.5">
          {headerExtra}
          <MaximizeButton onClick={onMaximize} label={title} />
        </div>
      </CardHeader>
      <CardContent className={cn("min-h-0 flex-1 overflow-hidden p-3", bodyClassName)}>
        {children}
      </CardContent>
    </Card>
  );
}

/** The scrolling text body shared by the inline terminal and its maximized view. */
function TerminalBody({
  lines,
  empty,
  renderLine,
  scrollable,
}: {
  lines: FeedLine[];
  empty: string;
  renderLine?: (line: FeedLine) => React.ReactNode;
  scrollable?: boolean;
}) {
  const scrollRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const node = scrollRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [lines]);

  return (
    <div
      ref={scrollRef}
      className={cn(
        "h-full bg-[oklch(0.16_0.01_250)] p-3 font-mono text-[11px] leading-relaxed text-[oklch(0.9_0.02_150)]",
        scrollable ? "overflow-auto" : "overflow-hidden",
      )}
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
  );
}

function TerminalPanel({
  title,
  icon: Icon,
  lines,
  empty,
  renderLine,
  className,
  statusDot,
  onMaximize,
}: {
  title: string;
  icon: React.ElementType;
  lines: FeedLine[];
  empty: string;
  renderLine?: (line: FeedLine) => React.ReactNode;
  className?: string;
  statusDot?: React.ReactNode;
  onMaximize: () => void;
}) {
  return (
    <Card className={cn("flex min-h-0 flex-col gap-0 overflow-hidden py-0", className)}>
      <CardHeader className="flex shrink-0 flex-row items-center justify-between gap-2 border-b border-border/60 px-3 py-2">
        <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Icon className="size-3.5" />
          {title}
          <span className="text-muted-foreground/50">· {lines.length}</span>
        </CardTitle>
        <div className="flex items-center gap-1.5">
          {statusDot}
          <MaximizeButton onClick={onMaximize} label={title} />
        </div>
      </CardHeader>
      <CardContent className="min-h-0 flex-1 overflow-hidden p-0">
        <TerminalBody lines={lines} empty={empty} renderLine={renderLine} />
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
  const [maximized, setMaximized] = React.useState<SectionKind | null>(null);

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
  const effectiveCategory =
    activeCategory ?? (categories.length > 0 ? categories[0] : null);

  const visibleCases = cases.filter(
    (runCase) =>
      (categoryByTestCase.get(runCase.test_case_id) ?? "Uncategorized") ===
      effectiveCategory,
  );

  const traceRunning = stream.traceState === "running";
  const traceActive =
    stream.traceState === "running" || stream.traceState === "paused";

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

  const traceDot = (
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
  );

  const liveDot = (
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
  );

  // ---- Reusable section bodies (rendered inline AND in the maximized dialog) ----

  const configBody = (
    <div className="flex flex-col gap-2.5">
      <div className="grid grid-cols-3 gap-2">
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
        <div className="flex flex-col justify-center gap-1">
          <ToggleField
            label="FD"
            checked={config.fd}
            onChange={(v) => patch({ fd: v })}
          />
          <ToggleField
            label="Recv own"
            checked={config.receive_own_messages}
            onChange={(v) => patch({ receive_own_messages: v })}
          />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-border/60 pt-2.5">
        <Button
          size="xs"
          onClick={onStartTrace}
          disabled={busy !== null || traceRunning}
          className="gap-1"
        >
          {busy === "trace-start" ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <Play className="size-3" />
          )}
          Start trace
        </Button>
        <Button
          size="xs"
          variant="outline"
          onClick={onStopTrace}
          disabled={busy !== null || !traceActive}
          className="gap-1"
        >
          <Square className="size-3" />
          Stop
        </Button>
        <Button
          size="xs"
          variant="outline"
          onClick={onTestConnection}
          disabled={busy !== null}
          className="gap-1"
        >
          {busy === "test-conn" ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <Plug className="size-3" />
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
    </div>
  );

  const messageBody = (
    <div className="grid grid-cols-2 gap-2">
      <div className="col-span-2 flex flex-col gap-0.5">
        <Label className="text-[10px] text-muted-foreground">Msg to send</Label>
        <Input
          value={manualMessage}
          onChange={(event) => setManualMessage(event.target.value)}
          placeholder="02 10 03 00 00 00 00 00"
          className="h-7 font-mono text-xs"
        />
      </div>
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
  );

  const renderCases = (scrollable: boolean) => (
    <div className="flex h-full min-h-0 flex-col gap-2.5">
      {categories.length > 0 && (
        <div className="flex shrink-0 flex-wrap gap-1.5">
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

      <div
        className={cn(
          "flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1 [scrollbar-color:var(--border)_transparent] [scrollbar-width:thin]",
          scrollable ? "" : "max-h-[260px]",
        )}
      >
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
                className="flex shrink-0 items-center gap-2 rounded-lg border border-border/60 bg-card p-2"
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
    </div>
  );

  const feedRenderLine = (line: FeedLine) => {
    const label = line.scope === "case" ? caseLabel(line.caseId) : "trace";
    return (
      <>
        <span className="text-[oklch(0.65_0.03_250)]">[{label}]</span>{" "}
        {line.line}
      </>
    );
  };

  const MAX_TITLE: Record<SectionKind, string> = {
    config: "Vector Config",
    message: "Message & IDs",
    cases: "Test cases",
    feed: "Live feed — trace window & test case scripts",
    terminal: "Python terminal — script status",
  };

  const maximizedBody = (() => {
    switch (maximized) {
      case "config":
        return <div className="h-full overflow-auto p-4">{configBody}</div>;
      case "message":
        return <div className="h-full overflow-auto p-4">{messageBody}</div>;
      case "cases":
        return <div className="h-full overflow-hidden p-4">{renderCases(true)}</div>;
      case "feed":
        return (
          <TerminalBody
            scrollable
            lines={stream.feed}
            empty="Start the trace or a test case to see live output here."
            renderLine={feedRenderLine}
          />
        );
      case "terminal":
        return (
          <TerminalBody
            scrollable
            lines={stream.terminal}
            empty="Process status (started, paused, exited, errors) appears here."
          />
        );
      default:
        return null;
    }
  })();

  return (
    <>
      <div className={cn("flex min-h-0 flex-col gap-2.5 lg:flex-row", className)}>
        {/* LEFT: controls */}
        <div className="flex min-h-0 flex-col gap-2.5 lg:w-[360px] lg:shrink-0">
          <Section
            title="Vector Config"
            onMaximize={() => setMaximized("config")}
            headerExtra={traceDot}
            className="shrink-0"
          >
            {configBody}
          </Section>

          <Section
            title="Message & IDs"
            onMaximize={() => setMaximized("message")}
            className="shrink-0"
          >
            {messageBody}
          </Section>

          <Section
            title="Test cases"
            onMaximize={() => setMaximized("cases")}
            className="min-h-0 flex-1"
            bodyClassName="p-3"
          >
            {renderCases(false)}
          </Section>
        </div>

        {/* RIGHT: live feed + python terminal — match the controls' height */}
        <div className="flex min-h-0 flex-1 flex-col gap-2.5 max-lg:h-[520px] lg:min-h-[440px]">
          <TerminalPanel
            className="flex-1"
            title="Live feed — trace window & test case scripts"
            icon={Radio}
            lines={stream.feed}
            empty="Start the trace or a test case to see live output here."
            statusDot={liveDot}
            renderLine={feedRenderLine}
            onMaximize={() => setMaximized("feed")}
          />
          <TerminalPanel
            className="flex-1"
            title="Python terminal — script status"
            icon={Terminal}
            lines={stream.terminal}
            empty="Process status (started, paused, exited, errors) appears here."
            onMaximize={() => setMaximized("terminal")}
          />
        </div>
      </div>

      <Dialog
        open={maximized !== null}
        onOpenChange={(open) => !open && setMaximized(null)}
      >
        <DialogContent className="flex h-[85vh] w-[92vw] max-w-5xl flex-col gap-0 overflow-hidden p-0 sm:max-w-5xl">
          <DialogHeader className="shrink-0 border-b border-border/60 px-4 py-3 text-left">
            <DialogTitle className="text-sm">
              {maximized ? MAX_TITLE[maximized] : ""}
            </DialogTitle>
          </DialogHeader>
          <div className="min-h-0 flex-1 overflow-hidden">{maximizedBody}</div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function StatusBadge({ status, proc }: { status: string; proc?: string }) {
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
