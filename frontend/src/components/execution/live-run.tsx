"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  FlaskConical,
  Loader2,
  Play,
  RotateCcw,
  SkipForward,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  cancelRun,
  createExecutionRun,
  formatDurationMs,
  notifyRunFinished,
  resumeRun,
  retryFailedCase,
  skipFailedCase,
  type ExecutionCase,
  type ExecutionRun,
  type RunSummary,
} from "@/lib/execution";
import { useExecutionStream } from "@/hooks/use-execution-stream";
import { CaseRail, CaseRailFallback } from "@/components/execution/case-rail";
import { StreamPanel } from "@/components/execution/stream-panel";

interface LiveRunProps {
  projectId: number;
  runId: number;
  initialRun: ExecutionRun;
  initialCases: ExecutionCase[];
  durationPerCaseS: number;
}

export function LiveRun({ projectId, runId, initialRun, initialCases, durationPerCaseS }: LiveRunProps) {
  const router = useRouter();
  const stream = useExecutionStream(runId);
  const [busy, setBusy] = React.useState<string | null>(null);
  const [activeCaseId, setActiveCaseId] = React.useState<number | null>(null);
  const notifiedRef = React.useRef(false);

  const run = stream.run ?? initialRun;
  const cases = stream.cases.length > 0 ? stream.cases : initialCases;
  const summary = stream.summary;

  const activeCase = React.useMemo(() => {
    if (activeCaseId !== null) {
      const found = cases.find((c) => c.id === activeCaseId);
      if (found) return found;
    }
    return (
      cases.find((c) => c.status === "running") ??
      cases.find((c) => c.status === "failed") ??
      cases[cases.length - 1] ??
      null
    );
  }, [cases, activeCaseId]);

  React.useEffect(() => {
    if (run.status === "completed" || run.status === "failed" || run.status === "cancelled") {
      if (!notifiedRef.current) {
        notifiedRef.current = true;
        if (summary) {
          notifyRunFinished(run, summary);
        } else {
          if (run.status === "completed") toast.success("Run completed");
          else if (run.status === "failed") toast.error("Run finished with failures");
          else toast.warning("Run cancelled");
        }
      }
    }
  }, [run.status, summary, run]);

  const failedCase = cases.find((c) => c.status === "failed") ?? null;
  const doneCount = cases.filter((c) => ["passed", "failed", "skipped"].includes(c.status)).length;
  const overall = run.total_cases > 0 ? Math.round((100 * doneCount) / run.total_cases) : 0;

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

  const onRetry = () =>
    guard("retry", async () => {
      await retryFailedCase(runId);
      toast.info("Retrying failed case", {
        description: failedCase ? `Restarting #${failedCase.position} with a fresh stream.` : undefined,
      });
    });

  const onSkip = () =>
    guard("skip", async () => {
      await skipFailedCase(runId);
      toast.warning("Skipped failed case", {
        description: "Continuing with the next test case.",
      });
    });

  const onResume = () =>
    guard("resume", async () => {
      await resumeRun(runId);
      toast.info("Run resumed");
    });

  const onCancel = () =>
    guard("cancel", async () => {
      await cancelRun(runId);
      toast.warning("Run cancelled");
    });

  const onRerun = () =>
    guard("rerun", async () => {
      const created = await createExecutionRun({
        projectId,
        testCaseIds: initialCases.map((c) => c.test_case_id),
        durationPerCaseS,
      });
      toast.success("New run started");
      router.push(`/projects/${projectId}/runs/${created.run.id}`);
    });

  const terminal = run.status === "completed" || run.status === "failed" || run.status === "cancelled";

  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 text-sm">
              <FlaskConical className="size-4 text-muted-foreground" />
              <span className="font-medium">
                Run #{runId}
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="capitalize text-muted-foreground">{run.status}</span>
              <span className="text-muted-foreground">·</span>
              <span className="font-tabular text-muted-foreground">
                {doneCount}/{run.total_cases} cases · {overall}%
              </span>
            </div>
            <Progress value={overall} className="h-1.5 w-64 max-w-full" />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {run.status === "paused" && failedCase && (
              <>
                <Button size="sm" onClick={onRetry} disabled={busy !== null} className="gap-1.5">
                  {busy === "retry" ? <Loader2 className="size-3.5 animate-spin" /> : <RotateCcw className="size-3.5" />}
                  Try again
                </Button>
                <Button size="sm" variant="outline" onClick={onSkip} disabled={busy !== null} className="gap-1.5">
                  {busy === "skip" ? <Loader2 className="size-3.5 animate-spin" /> : <SkipForward className="size-3.5" />}
                  Skip case
                </Button>
              </>
            )}
            {run.status === "paused" && !failedCase && (
              <Button size="sm" onClick={onResume} disabled={busy !== null} className="gap-1.5">
                {busy === "resume" ? <Loader2 className="size-3.5 animate-spin" /> : <Play className="size-3.5" />}
                Resume
              </Button>
            )}
            {!terminal && (
              <Button size="sm" variant="outline" onClick={onCancel} disabled={busy !== null} className="gap-1.5">
                {busy === "cancel" ? <Loader2 className="size-3.5 animate-spin" /> : <Ban className="size-3.5" />}
                Cancel
              </Button>
            )}
            {terminal && (
              <>
                <Button size="sm" variant="outline" onClick={() => router.push(`/projects/${projectId}/runs/${runId}/report`)} className="gap-1.5">
                  View report
                </Button>
                <Button size="sm" onClick={onRerun} disabled={busy !== null} className="gap-1.5">
                  {busy === "rerun" ? <Loader2 className="size-3.5 animate-spin" /> : <RotateCcw className="size-3.5" />}
                  Run again
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {run.status === "paused" && failedCase && (
        <div role="alert" className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
          <div className="space-y-1">
            <p className="font-medium text-destructive">
              Case #{failedCase.position} failed — execution paused
            </p>
            <p className="text-xs text-muted-foreground">
              {failedCase.error ?? "The ECU stopped acknowledging frames."} Nothing after this
              case has run. Retry restarts #{failedCase.position} with a fresh stream; skip marks
              it skipped and continues.
            </p>
          </div>
        </div>
      )}

      {terminal && summary && (
        <div className="flex items-start gap-3 rounded-lg border p-4 text-sm">
          {run.status === "completed" ? (
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600" />
          ) : (
            <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" />
          )}
          <div className="space-y-1">
            <p className="font-medium">
              {run.status === "completed"
                ? `Completed — all ${summary.total_cases} cases passed`
                : run.status === "cancelled"
                  ? "Run cancelled"
                  : `Finished with ${summary.failed_cases} failure${summary.failed_cases === 1 ? "" : "s"}`}
            </p>
            <p className="text-xs text-muted-foreground">
              {summary.packets_sent.toLocaleString()} frames · {summary.ack_rate_pct}% ACK ·
              total {formatDurationMs(summary.total_duration_ms)}
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            Test cases ({cases.length})
          </h2>
          {cases.length > 0 ? (
            <CaseRail cases={cases} activeCaseId={activeCase?.id ?? null} onSelect={setActiveCaseId} />
          ) : (
            <CaseRailFallback />
          )}
        </div>
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">
            {activeCase ? `Stream — case #${activeCase.position}` : "Stream"}
          </h2>
          <StreamPanel
            packets={stream.packets}
            cases={cases}
            connected={stream.connected}
            activeCaseId={activeCase?.id ?? null}
          />
        </div>
      </div>
    </div>
  );
}

export type { RunSummary };
