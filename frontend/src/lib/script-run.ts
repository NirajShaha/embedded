import { API_URL } from "@/config";
import type { ExecutionCase, ExecutionRun } from "@/lib/execution";

export interface VectorConfig {
  interface: string;
  channel: number;
  app_name: string;
  fd: boolean;
  bitrate: number;
  dbitrate: number;
  receive_own_messages: boolean;
}

export const DEFAULT_VECTOR_CONFIG: VectorConfig = {
  interface: "vector",
  channel: 0,
  app_name: "Python",
  fd: true,
  bitrate: 500000,
  dbitrate: 2000000,
  receive_own_messages: true,
};

export type ProcState = "running" | "paused" | "exited" | "error";

export type ScriptStreamFrame =
  | { type: "hello"; run_id: number }
  | { type: "snapshot"; run: ExecutionRun; cases: ExecutionCase[] }
  | {
      type: "output";
      scope: "trace" | "case";
      case_id: number | null;
      line: string;
      ts: string;
    }
  | {
      type: "status";
      scope: "trace" | "case";
      case_id: number | null;
      label: string;
      state: ProcState;
      exit_code: number | null;
      ts: string;
    };

export const TRACE_FRAME_RE =
  /^\s*(\d+(?:\.\d+)?)\s+(\S+)\s+([0-9A-Fa-f]+)\s+([A-Za-z]+)\s+(\S+)\s+(\d+)\s*(.*)$/;

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

export async function createScriptRun(payload: {
  projectId: number;
  testCaseIds: number[];
}): Promise<{ run: ExecutionRun; cases: ExecutionCase[] }> {
  return authedFetch("/executions/script-runs", {
    method: "POST",
    body: JSON.stringify({
      project_id: payload.projectId,
      test_case_ids: payload.testCaseIds,
    }),
  });
}

export async function testConnection(
  runId: number,
  config: VectorConfig,
): Promise<{ ok: boolean; message: string }> {
  return authedFetch(`/executions/${runId}/test-connection`, {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function startTrace(runId: number, config: VectorConfig) {
  return authedFetch(`/executions/${runId}/trace/start`, {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function stopTrace(runId: number) {
  return authedFetch(`/executions/${runId}/trace/stop`, { method: "POST" });
}

export async function startCase(
  runId: number,
  caseId: number,
  payload: {
    config: VectorConfig;
    sourceId?: string;
    destinationId?: string;
    manualMessage?: string;
  },
): Promise<{ case: ExecutionCase }> {
  return authedFetch(`/executions/${runId}/cases/${caseId}/start`, {
    method: "POST",
    body: JSON.stringify({
      config: payload.config,
      source_id: payload.sourceId || null,
      destination_id: payload.destinationId || null,
      manual_message: payload.manualMessage || null,
    }),
  });
}

export async function pauseCase(runId: number, caseId: number) {
  return authedFetch(`/executions/${runId}/cases/${caseId}/pause`, {
    method: "POST",
  });
}

export async function resumeCase(runId: number, caseId: number) {
  return authedFetch(`/executions/${runId}/cases/${caseId}/resume`, {
    method: "POST",
  });
}

export async function stopCase(runId: number, caseId: number) {
  return authedFetch(`/executions/${runId}/cases/${caseId}/stop`, {
    method: "POST",
  });
}

export function scriptStreamUrl(runId: number): string {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") ?? "" : "";
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/executions/${runId}/script-stream?token=${encodeURIComponent(token)}`;
}
