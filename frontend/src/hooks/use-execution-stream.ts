"use client";

import * as React from "react";

import {
  executionSocketUrl,
  type ExecutionCase,
  type ExecutionRun,
  type PacketFrame,
  type RunSummary,
} from "@/lib/execution";

export type StreamFrame =
  | { type: "hello" }
  | { type: "snapshot"; run: ExecutionRun; cases: ExecutionCase[] }
  | { type: "replay"; packets: PacketFrame[] }
  | { type: "run_started"; run: ExecutionRun }
  | { type: "case_started"; case: ExecutionCase }
  | { type: "case_progress"; case: ExecutionCase }
  | { type: "case_finished"; case: ExecutionCase }
  | { type: "run_paused"; run: ExecutionRun; failed_case: ExecutionCase }
  | { type: "run_finished"; run: ExecutionRun; summary: RunSummary }
  | { type: "run_cancelled"; run: ExecutionRun }
  | { type: "ping" }
  | { type: "error"; message: string }
  | ({ type: "packet" } & PacketFrame);

interface StreamState {
  run: ExecutionRun | null;
  cases: ExecutionCase[];
  packets: PacketFrame[];
  summary: RunSummary | null;
  connected: boolean;
  reconnects: number;
  lastEventAt: number | null;
}

const MAX_PACKETS = 400;

function applyFrame(state: StreamState, frame: StreamFrame): StreamState {
  switch (frame.type) {
    case "snapshot":
      return { ...state, run: frame.run, cases: frame.cases };
    case "replay":
      return { ...state, packets: [...frame.packets].slice(-MAX_PACKETS) };
    case "run_started":
      return { ...state, run: frame.run };
    case "case_started":
      return {
        ...state,
        cases: state.cases.map((item) =>
          item.id === frame.case.id ? frame.case : item,
        ),
        run: state.run
          ? { ...state.run, current_position: frame.case.position }
          : state.run,
      };
    case "case_progress":
    case "case_finished":
      return {
        ...state,
        cases: state.cases.map((item) =>
          item.id === frame.case.id ? frame.case : item,
        ),
      };
    case "run_paused":
    case "run_cancelled":
      return { ...state, run: frame.run };
    case "run_finished":
      return { ...state, run: frame.run, summary: frame.summary };
    default:
      return state;
  }
}

function backoff(attempt: number): number {
  return Math.min(10000, 750 * 2 ** Math.min(attempt, 4));
}

export function useExecutionStream(runId: number | null) {
  const [state, setState] = React.useState<StreamState>({
    run: null,
    cases: [],
    packets: [],
    summary: null,
    connected: false,
    reconnects: 0,
    lastEventAt: null,
  });

  React.useEffect(() => {
    if (runId === null) return;
    let socket: WebSocket | null = null;
    let closed = false;
    let attempt = 0;
    let timer: number | null = null;

    const connect = () => {
      if (closed) return;
      const url = executionSocketUrl(runId);
      const ws = new WebSocket(url);
      socket = ws;

      ws.onopen = () => {
        attempt = 0;
        setState((prev) => ({ ...prev, connected: true }));
      };

      ws.onmessage = (event: MessageEvent<string>) => {
        try {
          const frame = JSON.parse(event.data) as StreamFrame;
          if ((frame as { type: string }).type === "packet") {
            const packet = frame as unknown as PacketFrame;
            setState((prev) => ({
              ...applyFrame(prev, frame),
              packets: [...prev.packets, packet].slice(-MAX_PACKETS),
              lastEventAt: Date.now(),
            }));
            return;
          }
          if (frame.type === "ping" || frame.type === "hello") return;
          setState((prev) => ({
            ...applyFrame(prev, frame),
            lastEventAt: Date.now(),
          }));
        } catch {
          /* ignore malformed frames */
        }
      };

      ws.onerror = () => {
        try {
          ws.close();
        } catch {
          /* noop */
        }
      };

      ws.onclose = () => {
        setState((prev) => ({ ...prev, connected: false }));
        if (closed) return;
        attempt += 1;
        setState((prev) => ({ ...prev, reconnects: attempt }));
        timer = window.setTimeout(connect, backoff(attempt));
      };
    };

    connect();
    return () => {
      closed = true;
      if (timer !== null) window.clearTimeout(timer);
      try {
        socket?.close();
      } catch {
        /* noop */
      }
    };
  }, [runId]);

  const reset = React.useCallback(() => {
    setState({
      run: null,
      cases: [],
      packets: [],
      summary: null,
      connected: false,
      reconnects: 0,
      lastEventAt: null,
    });
  }, []);

  return { ...state, reset };
}
