import * as React from "react";
import { toast } from "sonner";

import { API_URL } from "@/config";

export type RunStatus =
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type CaseStatus =
  | "pending"
  | "running"
  | "passed"
  | "failed"
  | "skipped";

export interface ExecutionRun {
  id: number;
  project_id: number;
  status: RunStatus;
  total_cases: number;
  completed_cases: number;
  passed_cases: number;
  failed_cases: number;
  current_position: number | null;
  started_at: string | null;
  finished_at: string | null;
  created_by: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ExecutionCase {
  id: number;
  run_id: number;
  position: number;
  test_case_id: number;
  test_case_name: string | null;
  status: CaseStatus;
  attempt: number;
  packets_planned: number;
  packets_sent: number;
  packets_acked: number;
  packets_nacked: number;
  avg_rtt_ms: number | null;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  error: string | null;
  fault_start_seq: number | null;
  fault_end_seq: number | null;
}

export interface PacketFrame {
  type: "packet";
  run_id: number;
  case_id: number;
  position?: number;
  test_case_id?: number;
  seq: number;
  payload_hex: string;
  ack: boolean;
  rtt_ms: number;
  sent_at: string;
}

export interface RunSummary {
  run_id: number;
  status: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  packets_sent: number;
  packets_acked: number;
  packets_nacked: number;
  ack_rate_pct: number;
  total_duration_ms: number;
  avg_rtt_ms: number | null;
  by_status: Record<string, number>;
  finished_at: string | null;
}

export interface CaseBucket {
  position: number;
  test_case_id: number;
  bucket_index: number;
  packets: number;
  acked: number;
  nacked: number;
  avg_rtt_ms: number | null;
}

export interface RunEvent {
  event_type: string;
  payload: unknown;
  created_at: string | null;
}

export interface RunReport {
  run: ExecutionRun;
  cases: ExecutionCase[];
  summary: RunSummary;
  buckets: CaseBucket[];
  events: RunEvent[];
}

async function authedFetch(path: string, init?: RequestInit) {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string" && body.detail.trim()) {
        detail = body.detail;
      }
    } catch {
      /* keep fallback */
    }
    throw new Error(detail);
  }
  return response.json();
}

export async function createExecutionRun(payload: {
  projectId: number;
  testCaseIds: number[];
  durationPerCaseS?: number;
  packetLossRate?: number;
}): Promise<{ run: ExecutionRun; cases: ExecutionCase[] }> {
  return authedFetch("/executions", {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.projectId,
      test_case_ids: payload.testCaseIds,
      duration_per_case_s: payload.durationPerCaseS ?? 90,
      packet_loss_rate: payload.packetLossRate ?? 0.02,
    }),
  });
}

export async function getExecutionRun(
  runId: number,
): Promise<{ run: ExecutionRun; cases: ExecutionCase[] }> {
  return authedFetch(`/executions/${runId}`);
}

export async function getRunReport(runId: number): Promise<RunReport> {
  return authedFetch(`/executions/${runId}/report`);
}

export async function resumeRun(runId: number) {
  return authedFetch(`/executions/${runId}/resume`, { method: "POST" });
}

export async function retryFailedCase(runId: number) {
  return authedFetch(`/executions/${runId}/retry`, { method: "POST" });
}

export async function skipFailedCase(runId: number) {
  return authedFetch(`/executions/${runId}/skip`, { method: "POST" });
}

export async function cancelRun(runId: number) {
  return authedFetch(`/executions/${runId}/cancel`, { method: "POST" });
}

export function executionSocketUrl(runId: number): string {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") ?? "" : "";
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/executions/${runId}/stream?token=${encodeURIComponent(token)}`;
}

export function notifyRunFinished(run: ExecutionRun, summary: RunSummary) {
  const failed = summary.failed_cases > 0;
  const skipped = (summary.by_status.skipped ?? 0) > 0;
  if (run.status === "cancelled") {
    toast.warning("Run cancelled", {
      description: `${summary.passed_cases}/${summary.total_cases} cases passed before cancel.`,
    });
    return;
  }
  if (failed) {
    toast.error("Run finished with failures", {
      description: `${summary.passed_cases} passed, ${summary.failed_cases} failed${skipped ? `, ${summary.by_status.skipped} skipped` : ""}.`,
    });
    return;
  }
  toast.success("Run completed", {
    description: `All ${summary.total_cases} test cases passed. Ack rate ${summary.ack_rate_pct}%.`,
  });
}

export function formatDurationMs(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

export function formatClock(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function useNow(enabled: boolean, intervalMs = 1000): number {
  const [now, setNow] = React.useState(() => Date.now());
  React.useEffect(() => {
    if (!enabled) return;
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [enabled, intervalMs]);
  return now;
}
