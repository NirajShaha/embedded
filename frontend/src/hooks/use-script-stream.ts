"use client";

import * as React from "react";

import type { ExecutionCase } from "@/lib/execution";
import {
  scriptStreamUrl,
  TRACE_FRAME_RE,
  type ProcState,
  type ScriptStreamFrame,
} from "@/lib/script-run";

const MAX_LINES = 1000;

export interface FeedLine {
  id: number;
  scope: "trace" | "case";
  caseId: number | null;
  line: string;
}

export interface CaseProcState {
  state: ProcState;
  exitCode: number | null;
}

interface ScriptStreamState {
  connected: boolean;
  cases: ExecutionCase[];
  feed: FeedLine[];
  terminal: FeedLine[];
  traceState: ProcState | null;
  caseStates: Record<number, CaseProcState>;
}

const INITIAL: ScriptStreamState = {
  connected: false,
  cases: [],
  feed: [],
  terminal: [],
  traceState: null,
  caseStates: {},
};

function backoff(attempt: number): number {
  return Math.min(10000, 750 * 2 ** Math.min(attempt, 4));
}

export function useScriptStream(runId: number | null) {
  const [state, setState] = React.useState<ScriptStreamState>(INITIAL);
  const counter = React.useRef(0);

  React.useEffect(() => {
    if (runId === null) return;
    let socket: WebSocket | null = null;
    let closed = false;
    let attempt = 0;
    let timer: number | null = null;

    const connect = () => {
      if (closed) return;
      const ws = new WebSocket(scriptStreamUrl(runId));
      socket = ws;

      ws.onopen = () => {
        attempt = 0;
        setState((prev) => ({ ...prev, connected: true }));
      };

      ws.onmessage = (event: MessageEvent<string>) => {
        let frame: ScriptStreamFrame;
        try {
          frame = JSON.parse(event.data) as ScriptStreamFrame;
        } catch {
          return;
        }
        setState((prev) => {
          switch (frame.type) {
            case "snapshot":
              return { ...prev, cases: frame.cases };
            case "output": {
              const id = (counter.current += 1);
              const entry = {
                id,
                scope: frame.scope,
                caseId: frame.case_id,
                line: frame.line,
              };
              // Keep trace errors and status text in the terminal, not the frame table.
              if (frame.scope === "trace" && TRACE_FRAME_RE.test(frame.line)) {
                const feed = [...prev.feed, entry].slice(-MAX_LINES);
                return { ...prev, feed };
              }
              const terminal = [...prev.terminal, entry].slice(-MAX_LINES);
              return { ...prev, terminal };
            }
            case "status": {
              const id = (counter.current += 1);
              const codePart =
                frame.exit_code !== null ? ` (code ${frame.exit_code})` : "";
              const terminal = [
                ...prev.terminal,
                {
                  id,
                  scope: frame.scope,
                  caseId: frame.case_id,
                  line: `${frame.label}: ${frame.state}${codePart}`,
                },
              ].slice(-MAX_LINES);
              const next: ScriptStreamState = { ...prev, terminal };
              if (frame.scope === "trace") {
                next.traceState = frame.state;
              } else if (frame.case_id !== null) {
                next.caseStates = {
                  ...prev.caseStates,
                  [frame.case_id]: {
                    state: frame.state,
                    exitCode: frame.exit_code,
                  },
                };
              }
              return next;
            }
            default:
              return prev;
          }
        });
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

  return state;
}
