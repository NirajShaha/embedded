"use client";

import * as React from "react";

import type { FeedLine } from "@/hooks/use-script-stream";

const MAX_LINES = 1000;

const REQUESTS = [
  "02 10 03 00 00 00 00 00",
  "02 10 01 00 00 00 00 00",
  "03 22 F1 90 00 00 00 00",
  "02 3E 00 00 00 00 00 00",
  "02 27 01 00 00 00 00 00",
  "03 22 F1 87 00 00 00 00",
];

const RESPONSES = [
  "06 50 03 00 32 01 F4 AA",
  "04 62 F1 90 12 34 00 00",
  "03 7F 10 78 00 00 00 00",
  "04 6E F1 90 AA BB 00 00",
  "02 7E 00 00 00 00 00 00",
  "04 67 01 34 12 00 00 00",
];

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hexByte(value: number): string {
  return value.toString(16).toUpperCase().padStart(2, "0");
}

function frame(
  ts: number,
  id: number,
  dir: "Tx" | "Rx",
  fd: boolean,
  data: string,
): string {
  const dlc = data.split(" ").length;
  const stamp = ts.toFixed(6).padStart(10, " ");
  const idHex = id.toString(16).toUpperCase().padStart(3, "0");
  return `${stamp} 1 ${idHex} ${dir} ${fd ? "fd" : "d"} ${dlc} ${data}`;
}

export function useDummyStream(active: boolean, caseId: number | null) {
  const [feed, setFeed] = React.useState<FeedLine[]>([]);
  const [terminal, setTerminal] = React.useState<FeedLine[]>([]);
  const idRef = React.useRef(1_000_000);
  const caseRef = React.useRef<number | null>(caseId);
  const tsRef = React.useRef(1.2);
  const scanRef = React.useRef(0x400);
  const tickRef = React.useRef(0);
  const rngRef = React.useRef<(() => number) | null>(null);
  const startedRef = React.useRef(false);

  React.useEffect(() => {
    caseRef.current = caseId;
  }, [caseId]);

  React.useEffect(() => {
    if (!active) return;
    if (rngRef.current === null) rngRef.current = mulberry32(0xc0ffee);
    const rng = rngRef.current;
    const nextId = () => {
      idRef.current += 1;
      return idRef.current;
    };

    if (!startedRef.current) {
      startedRef.current = true;
      const cid = caseRef.current;
      setTerminal([
        { id: nextId(), scope: "trace", caseId: null, line: "[started] Trace window (trace_window.py)" },
        { id: nextId(), scope: "trace", caseId: null, line: "Trace Window Started" },
        { id: nextId(), scope: "trace", caseId: null, line: "base hex timestamps absolute" },
        { id: nextId(), scope: "case", caseId: cid, line: "[started] Find all UDS interfaces (diagnostic_id_scanner.py)" },
        { id: nextId(), scope: "case", caseId: cid, line: "Scan range 0x400 - 0x500 | request 02 10 03 00 00 00 00 00" },
        { id: nextId(), scope: "case", caseId: cid, line: "Starting Diagnostic ID Enumeration..." },
      ]);
    } else {
      setTerminal((prev) =>
        [
          ...prev,
          {
            id: nextId(),
            scope: "case" as const,
            caseId: caseRef.current,
            line: "[resumed] Dummy trace resumed",
          },
        ].slice(-MAX_LINES),
      );
    }

    const timer = window.setInterval(() => {
      tickRef.current += 1;
      const tick = tickRef.current;
      const liveCase = caseRef.current;
      tsRef.current += 0.018 + rng() * 0.045;
      let cur = tsRef.current;
      const src = 0x400 + ((scanRef.current - 0x400) % 0x101);
      scanRef.current += 1;

      const req = REQUESTS[tick % REQUESTS.length];
      const res = RESPONSES[tick % RESPONSES.length];
      const rxId = src + 0x08 <= 0x7ff ? src + 0x08 : src - 0x08;
      const frames: FeedLine[] = [
        { id: nextId(), scope: "trace", caseId: null, line: frame(cur, src, "Tx", false, req) },
        {
          id: nextId(),
          scope: "trace",
          caseId: null,
          line: frame(cur + 0.006 + rng() * 0.01, rxId, "Rx", false, res),
        },
      ];
      const bgCount = Math.floor(rng() * 3);
      for (let i = 0; i < bgCount; i += 1) {
        cur += 0.002 + rng() * 0.008;
        const bgId = 0x120 + Math.floor(rng() * 0x5d0);
        const fd = tick % 23 === 0 && i === 0;
        const count = fd ? 16 : 8;
        const parts: string[] = [];
        for (let b = 0; b < count; b += 1) {
          parts.push(hexByte(Math.floor(rng() * 256)));
        }
        frames.push({
          id: nextId(),
          scope: "trace",
          caseId: null,
          line: frame(cur, bgId, "Rx", fd, parts.join(" ")),
        });
      }
      tsRef.current = cur;
      setFeed((prev) => [...prev, ...frames].slice(-MAX_LINES));

      const notes: FeedLine[] = [];
      if (tick % 6 === 0) {
        notes.push({
          id: nextId(),
          scope: "case",
          caseId: liveCase,
          line: `Scanning 0x${src.toString(16).toUpperCase().padStart(3, "0")}`,
        });
      }
      if (tick % 17 === 0) {
        notes.push({
          id: nextId(),
          scope: "case",
          caseId: liveCase,
          line: `[+] Found: 0x${src.toString(16).toUpperCase().padStart(3, "0")} -> 0x${rxId.toString(16).toUpperCase().padStart(3, "0")}`,
        });
      }
      if (notes.length > 0) {
        setTerminal((prev) => [...prev, ...notes].slice(-MAX_LINES));
      }
    }, 260);

    return () => window.clearInterval(timer);
  }, [active]);

  return { feed, terminal, hasData: feed.length > 0 || terminal.length > 0 };
}
