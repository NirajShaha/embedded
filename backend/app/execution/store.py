"""Persistence helpers for the execution engine, via Prisma raw queries.

Execution tables are created as a Prisma migration so every environment gets
them automatically. Raw SQL (``query_raw``/``execute_raw``) keeps the new
tables out of the generated Prisma client until the next ``prisma generate``,
and mirrors DATETIME behaviour carefully (MySQL returns naive datetimes;
all API timestamps are normalised to UTC ISO strings at the boundary).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.prisma_client import db


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _now_sql() -> str:
    return "UTC_TIMESTAMP(6)"


async def fetch_run(run_id: int) -> dict[str, Any] | None:
    rows: Any = await db.query_raw(
        "SELECT * FROM `test_runs` WHERE `id` = ?",
        run_id,
    )
    if not rows:
        return None
    return dict(rows[0])


async def fetch_run_cases(run_id: int) -> list[dict[str, Any]]:
    rows: Any = await db.query_raw(
        "SELECT * FROM `test_run_cases` WHERE `run_id` = ? ORDER BY `position` ASC",
        run_id,
    )
    return [dict(row) for row in rows]


async def fetch_case(case_id: int) -> dict[str, Any] | None:
    rows: Any = await db.query_raw(
        "SELECT * FROM `test_run_cases` WHERE `id` = ?",
        case_id,
    )
    if not rows:
        return None
    return dict(rows[0])


async def fetch_recent_packets(run_id: int, limit: int) -> list[dict[str, Any]]:
    rows: Any = await db.query_raw(
        "SELECT `run_id`, `case_id`, `seq`, `payload_hex`, `ack`, `rtt_ms`, "
        "`sent_at` FROM `test_packets` WHERE `run_id` = ? "
        "ORDER BY `seq_global` DESC LIMIT ?",
        run_id,
        limit,
    )
    ordered = list(reversed([dict(row) for row in rows]))
    for row in ordered:
        row["sent_at"] = _iso(row.get("sent_at"))
    return ordered


async def fetch_case_buckets(run_id: int) -> list[dict[str, Any]]:
    rows: Any = await db.query_raw(
        "SELECT c.`position`, c.`test_case_id`, b.`bucket_index`, b.`packets`, "
        "b.`acked`, b.`nacked`, b.`avg_rtt_ms` "
        "FROM `test_case_buckets` b "
        "JOIN `test_run_cases` c ON c.`id` = b.`case_id` "
        "WHERE b.`run_id` = ? ORDER BY c.`position` ASC, b.`bucket_index` ASC",
        run_id,
    )
    return [dict(row) for row in rows]


async def fetch_run_events(run_id: int, limit: int = 200) -> list[dict[str, Any]]:
    rows: Any = await db.query_raw(
        "SELECT `event_type`, `payload`, `created_at` FROM `test_run_events` "
        "WHERE `run_id` = ? ORDER BY `id` DESC LIMIT ?",
        run_id,
        limit,
    )
    events = [dict(row) for row in rows]
    for event in events:
        event["created_at"] = _iso(event.get("created_at"))
    return list(reversed(events))


async def insert_run_event(
    run_id: int, event_type: str, payload: dict[str, Any]
) -> None:
    await db.execute_raw(
        "INSERT INTO `test_run_events` (`run_id`, `event_type`, `payload`, "
        f"`created_at`) VALUES (?, ?, ?, {_now_sql()})",
        run_id,
        event_type,
        json.dumps(payload, default=str),
    )


def serialize_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "project_id": int(row["project_id"]),
        "status": str(row["status"]),
        "total_cases": int(row["total_cases"]),
        "completed_cases": int(row["completed_cases"]),
        "passed_cases": int(row["passed_cases"]),
        "failed_cases": int(row["failed_cases"]),
        "current_position": (
            int(row["current_position"]) if row["current_position"] is not None else None
        ),
        "started_at": _iso(row.get("started_at")),
        "finished_at": _iso(row.get("finished_at")),
        "created_by": int(row["created_by"]) if row["created_by"] is not None else None,
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
    }


def serialize_case(row: dict[str, Any]) -> dict[str, Any]:
    fault_start = row.get("fault_start_seq")
    fault_end = row.get("fault_end_seq")
    return {
        "id": int(row["id"]),
        "run_id": int(row["run_id"]),
        "position": int(row["position"]),
        "test_case_id": int(row["test_case_id"]),
        "test_case_name": row.get("test_case_name"),
        "status": str(row["status"]),
        "attempt": int(row["attempt"]),
        "packets_planned": int(row["packets_planned"]),
        "packets_sent": int(row["packets_sent"]),
        "packets_acked": int(row["packets_acked"]),
        "packets_nacked": int(row["packets_nacked"]),
        "avg_rtt_ms": (
            float(row["avg_rtt_ms"]) if row["avg_rtt_ms"] is not None else None
        ),
        "started_at": _iso(row.get("started_at")),
        "finished_at": _iso(row.get("finished_at")),
        "duration_ms": (
            int(row["duration_ms"]) if row["duration_ms"] is not None else None
        ),
        "error": row.get("error"),
        "fault_start_seq": int(fault_start) if fault_start is not None else None,
        "fault_end_seq": int(fault_end) if fault_end is not None else None,
    }


def build_summary(run: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    packets_sent = sum(int(case["packets_sent"]) for case in cases)
    packets_acked = sum(int(case["packets_acked"]) for case in cases)
    packets_nacked = sum(int(case["packets_nacked"]) for case in cases)
    total_ms = sum(int(case["duration_ms"] or 0) for case in cases)
    rtts = [
        float(case["avg_rtt_ms"])
        for case in cases
        if case["avg_rtt_ms"] is not None
    ]
    avg_rtt = round(sum(rtts) / len(rtts), 2) if rtts else None
    ack_rate = (
        round(100.0 * packets_acked / packets_sent, 2) if packets_sent else 0.0
    )
    by_status: dict[str, int] = {}
    for case in cases:
        status = str(case["status"])
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "run_id": int(run["id"]),
        "status": str(run["status"]),
        "total_cases": int(run["total_cases"]),
        "passed_cases": int(run["passed_cases"]),
        "failed_cases": int(run["failed_cases"]),
        "packets_sent": packets_sent,
        "packets_acked": packets_acked,
        "packets_nacked": packets_nacked,
        "ack_rate_pct": ack_rate,
        "total_duration_ms": total_ms,
        "avg_rtt_ms": avg_rtt,
        "by_status": by_status,
        "finished_at": _iso(run.get("finished_at")),
    }
