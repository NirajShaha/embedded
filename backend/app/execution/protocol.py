"""WebSocket event contract for test-case execution streaming.

Every frame sent to ``/api/executions/{run_id}/stream`` is a JSON object with
a ``type`` discriminator. Control frames (snapshot, case_started,
case_finished, run_paused, run_finished) are delivered reliably; ``packet``
frames may be dropped for slow consumers (the drop is counted and exposed so
the UI can show a gap instead of silently showing stale data).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hello(run_id: int, resume: bool) -> dict[str, Any]:
    return {
        "type": "hello",
        "run_id": run_id,
        "resumed": resume,
        "server_time": utcnow_iso(),
    }


def snapshot(run: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "snapshot",
        "run": run,
        "cases": cases,
    }


def replay(packets: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "replay",
        "packets": packets,
    }


def run_started(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "run_started",
        "run": run,
    }


def case_started(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "case_started",
        "case": case,
    }


def packet(
    *,
    run_id: int,
    case_id: int,
    position: int,
    test_case_id: int,
    seq: int,
    payload_hex: str,
    ack: bool,
    rtt_ms: float,
    sent_at: str,
) -> dict[str, Any]:
    return {
        "type": "packet",
        "run_id": run_id,
        "case_id": case_id,
        "position": position,
        "test_case_id": test_case_id,
        "seq": seq,
        "payload_hex": payload_hex,
        "ack": ack,
        "rtt_ms": rtt_ms,
        "sent_at": sent_at,
    }


def case_progress(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "case_progress",
        "case": case,
    }


def case_finished(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "case_finished",
        "case": case,
    }


def run_paused(run: dict[str, Any], failed_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "run_paused",
        "run": run,
        "failed_case": failed_case,
    }


def run_finished(run: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "run_finished",
        "run": run,
        "summary": summary,
    }


def run_cancelled(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "run_cancelled",
        "run": run,
    }


def ping() -> dict[str, Any]:
    return {
        "type": "ping",
        "server_time": utcnow_iso(),
    }


def error(message: str) -> dict[str, Any]:
    return {
        "type": "error",
        "message": message,
    }
