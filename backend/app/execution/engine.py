"""Asyncio execution engine: one background task per run.

Resilience model
----------------
* **One writer per run** — an ``asyncio.Lock`` per run serialises state
  transitions, so concurrent REST calls (pause/resume/retry/cancel) and the
  worker task can never interleave a case transition.
* **Crash recovery** — packet progress is flushed to ``test_run_cases`` and
  per-second buckets to ``test_case_buckets`` every few seconds. On restart,
  ``recover_incomplete_runs`` marks orphaned ``running`` rows ``paused`` with a
  resume cursor; ``resume`` continues from the next uncompleted case and a
  retried case starts a fresh attempt with fresh seeds.
* **Bounded memory** — packets stream to WebSocket subscribers and to the DB;
  only a small ring buffer is kept in memory for replays and slow joiners.
* **Slow consumers don't stall the run** — each subscriber has a bounded
  queue; a full queue drops ``packet`` frames (counted as ``dropped``) while
  control frames are still delivered reliably.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.execution import protocol
from app.execution.settings import (
    BUCKET_FLUSH_EVERY_S,
    BUCKET_S,
    MAX_RUN_WALL_CLOCK_S,
    PACKET_INTERVAL_S,
    PACKET_RING_BUFFER,
    PACKET_SAMPLE_EVERY,
    WS_HEARTBEAT_S,
    WS_QUEUE_SIZE,
)
from app.execution.simulator import generate_packets
from app.execution.store import (
    fetch_case,
    fetch_recent_packets,
    fetch_run,
    fetch_run_cases,
    insert_run_event,
    serialize_case,
    serialize_run,
)
from app.prisma_client import db


@dataclass(eq=False)
class Subscriber:
    queue: asyncio.Queue = field(
        default_factory=lambda: asyncio.Queue(maxsize=WS_QUEUE_SIZE)
    )
    dropped: int = 0


@dataclass
class RunState:
    run_id: int
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    subscribers: set[Subscriber] = field(default_factory=set)
    ring: deque = field(default_factory=lambda: deque(maxlen=PACKET_RING_BUFFER))
    worker: asyncio.Task | None = None
    stop_requested: bool = False
    seq_global: int = 0


_states: dict[int, RunState] = {}
_states_lock = asyncio.Lock()


async def get_state(run_id: int) -> RunState:
    async with _states_lock:
        state = _states.get(run_id)
        if state is None:
            state = RunState(run_id=run_id)
            _states[run_id] = state
        return state


def packets_per_case(duration_s: float) -> int:
    return max(8, int(duration_s / PACKET_INTERVAL_S))


def case_duration_for_run(total_cases: int, duration_per_case_s: float) -> float:
    budget = MAX_RUN_WALL_CLOCK_S / max(1, total_cases)
    return min(duration_per_case_s, budget)


async def _broadcast(state: RunState, message: dict) -> None:
    dead: list[Subscriber] = []
    for sub in list(state.subscribers):
        try:
            if message.get("type") == "packet":
                try:
                    sub.queue.put_nowait(message)
                except asyncio.QueueFull:
                    sub.dropped += 1
            else:
                await sub.queue.put(message)
        except Exception:
            dead.append(sub)
    for sub in dead:
        state.subscribers.discard(sub)


async def subscribe(run_id: int) -> tuple[RunState, Subscriber]:
    state = await get_state(run_id)
    sub = Subscriber()
    state.subscribers.add(sub)
    return state, sub


def unsubscribe(state: RunState, sub: Subscriber) -> None:
    state.subscribers.discard(sub)


async def snapshot_payload(run_id: int) -> tuple[dict, list[dict]]:
    run = await fetch_run(run_id)
    if run is None:
        raise KeyError("run not found")
    cases = await fetch_run_cases(run_id)
    return serialize_run(run), [serialize_case(case) for case in cases]


async def start_worker(run_id: int) -> None:
    state = await get_state(run_id)
    async with state.lock:
        if state.worker is not None and not state.worker.done():
            return
        state.stop_requested = False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        state.worker = loop.create_task(_run_loop(run_id))


async def request_stop(run_id: int) -> None:
    state = await get_state(run_id)
    state.stop_requested = True


async def recover_incomplete_runs() -> int:
    """Mark orphaned running/paused rows resumable after a backend restart."""
    rows: list[dict] = await db.query_raw(
        "SELECT `id` FROM `test_runs` WHERE `status` IN ('running', 'paused')"
    )
    recovered = 0
    for row in rows:
        run_id = int(row["id"] if isinstance(row, dict) else row[0])
        run = await fetch_run(run_id)
        if run is None or str(run["status"]) not in {"running", "paused"}:
            continue
        cases = await fetch_run_cases(run_id)
        failed = next(
            (
                case
                for case in cases
                if str(case["status"]) == "failed"
                and int(case["position"]) == int(run["current_position"] or 0)
            ),
            None,
        )
        if failed is not None:
            await db.execute_raw(
                "UPDATE `test_runs` SET `status` = 'paused', "
                "`updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
                run_id,
            )
            await insert_run_event(
                run_id, "run_recovered", {"status": "paused", "reason": "restart"}
            )
        else:
            running_cases: list[dict] = await db.query_raw(
                "SELECT `id` FROM `test_run_cases` WHERE `run_id` = ? "
                "AND `status` = 'running'",
                run_id,
            )
            for item in running_cases:
                case_id = int(item["id"] if isinstance(item, dict) else item[0])
                await db.execute_raw(
                    "UPDATE `test_run_cases` SET `status` = 'pending', "
                    "`started_at` = NULL WHERE `id` = ?",
                    case_id,
                )
            await db.execute_raw(
                "UPDATE `test_runs` SET `status` = 'paused', "
                "`updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
                run_id,
            )
            await insert_run_event(
                run_id, "run_recovered", {"status": "paused", "reason": "restart"}
            )
        recovered += 1
    return recovered


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _set_case_started(case_id: int, attempt: int, planned: int) -> None:
    await db.execute_raw(
        "UPDATE `test_run_cases` SET `status` = 'running', `attempt` = ?, "
        "`packets_planned` = ?, `packets_sent` = 0, `packets_acked` = 0, "
        "`packets_nacked` = 0, `avg_rtt_ms` = NULL, `started_at` = UTC_TIMESTAMP(6), "
        "`finished_at` = NULL, `duration_ms` = NULL, `error` = NULL, "
        "`fault_start_seq` = NULL, `fault_end_seq` = NULL "
        "WHERE `id` = ?",
        attempt,
        planned,
        case_id,
    )


async def _flush_case_progress(
    *,
    case_id: int,
    sent: int,
    acked: int,
    nacked: int,
    avg_rtt: float | None,
) -> None:
    await db.execute_raw(
        "UPDATE `test_run_cases` SET `packets_sent` = ?, `packets_acked` = ?, "
        "`packets_nacked` = ?, `avg_rtt_ms` = ? WHERE `id` = ?",
        sent,
        acked,
        nacked,
        avg_rtt,
        case_id,
    )


async def _finish_case(
    *,
    case_id: int,
    run_id: int,
    status: str,
    sent: int,
    acked: int,
    nacked: int,
    avg_rtt: float | None,
    started_perf: float,
    fault_start: int | None,
    fault_end: int | None,
    error: str | None = None,
) -> dict:
    duration_ms = max(1, int((time.perf_counter() - started_perf) * 1000))
    await db.execute_raw(
        "UPDATE `test_run_cases` SET `status` = ?, `packets_sent` = ?, "
        "`packets_acked` = ?, `packets_nacked` = ?, `avg_rtt_ms` = ?, "
        "`finished_at` = UTC_TIMESTAMP(6), `duration_ms` = ?, `error` = ?, "
        "`fault_start_seq` = ?, `fault_end_seq` = ? WHERE `id` = ?",
        status,
        sent,
        acked,
        nacked,
        avg_rtt,
        duration_ms,
        error,
        fault_start,
        fault_end,
        case_id,
    )
    row = await fetch_case(case_id)
    assert row is not None
    return serialize_case(row)


async def _upsert_bucket(
    *,
    run_id: int,
    case_id: int,
    bucket_index: int,
    packets: int,
    acked: int,
    nacked: int,
    avg_rtt: float | None,
) -> None:
    await db.execute_raw(
        "INSERT INTO `test_case_buckets` (`run_id`, `case_id`, `bucket_index`, "
        "`packets`, `acked`, `nacked`, `avg_rtt_ms`) VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON DUPLICATE KEY UPDATE `packets` = VALUES(`packets`), "
        "`acked` = VALUES(`acked`), `nacked` = VALUES(`nacked`), "
        "`avg_rtt_ms` = VALUES(`avg_rtt_ms`)",
        run_id,
        case_id,
        bucket_index,
        packets,
        acked,
        nacked,
        avg_rtt,
    )


async def _update_run_counters(run_id: int) -> dict:
    cases = await fetch_run_cases(run_id)
    completed = sum(
        1 for case in cases if str(case["status"]) in {"passed", "failed", "skipped"}
    )
    passed = sum(1 for case in cases if str(case["status"]) == "passed")
    failed = sum(1 for case in cases if str(case["status"]) == "failed")
    current = next(
        (
            int(case["position"])
            for case in cases
            if str(case["status"]) in {"running", "failed"}
        ),
        None,
    )
    if current is None:
        pending = [
            int(case["position"]) for case in cases if str(case["status"]) == "pending"
        ]
        current = min(pending) if pending else None
    await db.execute_raw(
        "UPDATE `test_runs` SET `completed_cases` = ?, `passed_cases` = ?, "
        "`failed_cases` = ?, `current_position` = ?, "
        "`updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
        completed,
        passed,
        failed,
        current,
        run_id,
    )
    row = await fetch_run(run_id)
    assert row is not None
    return serialize_run(row)


async def _set_run_status(
    run_id: int, status: str, finished: bool = False
) -> dict:
    if finished:
        await db.execute_raw(
            "UPDATE `test_runs` SET `status` = ?, `finished_at` = UTC_TIMESTAMP(6), "
            "`updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
            status,
            run_id,
        )
    else:
        await db.execute_raw(
            "UPDATE `test_runs` SET `status` = ?, `updated_at` = UTC_TIMESTAMP(6) "
            "WHERE `id` = ?",
            status,
            run_id,
        )
    row = await fetch_run(run_id)
    assert row is not None
    return serialize_run(row)


async def _run_loop(run_id: int) -> None:
    state = await get_state(run_id)
    try:
        while True:
            run = await fetch_run(run_id)
            if run is None:
                return
            if state.stop_requested or str(run["status"]) in {
                "completed",
                "failed",
                "cancelled",
            }:
                return
            if str(run["status"]) == "paused":
                return

            cases = await fetch_run_cases(run_id)
            pending = [
                case for case in cases if str(case["status"]) == "pending"
            ]
            if not pending:
                async with state.lock:
                    fresh = await fetch_run(run_id)
                    if fresh is None or str(fresh["status"]) != "running":
                        return
                    remaining = [
                        case
                        for case in await fetch_run_cases(run_id)
                        if str(case["status"]) == "pending"
                    ]
                    if remaining:
                        pending = remaining
                    else:
                        failed_count = sum(
                            1
                            for case in await fetch_run_cases(run_id)
                            if str(case["status"]) == "failed"
                        )
                        final_status = (
                            "failed" if failed_count else "completed"
                        )
                        finished_run = await _set_run_status(
                            run_id, final_status, finished=True
                        )
                        await insert_run_event(
                            run_id,
                            "run_finished",
                            {"status": final_status},
                        )
                        from app.execution.store import build_summary

                        summary = build_summary(
                            finished_run,
                            [
                                serialize_case(case)
                                for case in await fetch_run_cases(run_id)
                            ],
                        )
                        await _broadcast(
                            state,
                            protocol.run_finished(finished_run, summary),
                        )
                        return

            case = pending[0]
            await _execute_case(run_id, state, int(case["id"]))
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 - a worker must never die silently
        try:
            paused = await _set_run_status(run_id, "paused")
            await insert_run_event(
                run_id, "run_error", {"message": str(exc)[:500]}
            )
            await _broadcast(state, protocol.error(f"Run paused: {exc}"))
            _ = paused
        except Exception:
            pass


async def _execute_case(run_id: int, state: RunState, case_id: int) -> None:
    case = await fetch_case(case_id)
    if case is None or str(case["status"]) != "pending":
        return
    run = await fetch_run(run_id)
    if run is None:
        return

    duration_s = case_duration_for_run(
        int(run["total_cases"]), float(run["duration_per_case_s"])
    )
    planned = packets_per_case(duration_s)
    attempt = int(case["attempt"]) + 1
    test_case_id = int(case["test_case_id"])

    await _set_case_started(case_id, attempt, planned)
    started = await fetch_case(case_id)
    assert started is not None
    await _update_run_counters(run_id)
    await insert_run_event(
        run_id,
        "case_started",
        {"case_id": case_id, "attempt": attempt, "planned": planned},
    )
    await _broadcast(state, protocol.case_started(serialize_case(started)))

    outcome, window, packets = generate_packets(
        run_id=run_id,
        test_case_id=test_case_id,
        attempt=attempt,
        packet_count=planned,
        packet_loss_rate=float(run["packet_loss_rate"]),
    )
    interval = duration_s / max(1, planned)

    sent = 0
    acked = 0
    nacked = 0
    rtt_sum = 0.0
    started_perf = time.perf_counter()
    last_flush = started_perf
    last_progress_emit = 0.0
    buckets: dict[int, dict[str, float]] = defaultdict(
        lambda: {"packets": 0, "acked": 0, "nacked": 0, "rtt": 0.0}
    )

    for spec in packets:
        if state.stop_requested:
            await _finish_case(
                case_id=case_id,
                run_id=run_id,
                status="pending",
                sent=sent,
                acked=acked,
                nacked=nacked,
                avg_rtt=(round(rtt_sum / sent, 2) if sent else None),
                started_perf=started_perf,
                fault_start=None,
                fault_end=None,
                error="interrupted",
            )
            await _update_run_counters(run_id)
            return
        fresh = await fetch_case(case_id)
        if fresh is None or str(fresh["status"]) != "running":
            return

        state.seq_global += 1
        sent += 1
        if spec.ack:
            acked += 1
        else:
            nacked += 1
        rtt_sum += spec.rtt_ms
        bucket_index = min(
            int((spec.seq - 1) * PACKET_INTERVAL_S / BUCKET_S),
            int(math.ceil(planned * PACKET_INTERVAL_S / BUCKET_S)),
        )
        bucket = buckets[bucket_index]
        bucket["packets"] += 1
        bucket["rtt"] += spec.rtt_ms
        if spec.ack:
            bucket["acked"] += 1
        else:
            bucket["nacked"] += 1

        frame = protocol.packet(
            run_id=run_id,
            case_id=case_id,
            position=int(case["position"]),
            test_case_id=test_case_id,
            seq=spec.seq,
            payload_hex=spec.payload.hex(),
            ack=spec.ack,
            rtt_ms=spec.rtt_ms,
            sent_at=_iso_now(),
        )
        state.ring.append(frame)
        await _broadcast(state, frame)
        should_store = (
            (not spec.ack)
            or spec.seq <= 2
            or spec.seq > planned - 2
            or spec.seq % PACKET_SAMPLE_EVERY == 0
        )
        if should_store:
            await db.execute_raw(
                "INSERT INTO `test_packets` (`run_id`, `case_id`, `seq`, "
                "`seq_global`, `payload_hex`, `ack`, `rtt_ms`, `sent_at`) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, UTC_TIMESTAMP(6))",
                run_id,
                case_id,
                spec.seq,
                state.seq_global,
                spec.payload.hex(),
                1 if spec.ack else 0,
                spec.rtt_ms,
            )

        now = time.perf_counter()
        if now - last_flush >= BUCKET_FLUSH_EVERY_S:
            avg = round(rtt_sum / sent, 2) if sent else None
            await _flush_case_progress(
                case_id=case_id,
                sent=sent,
                acked=acked,
                nacked=nacked,
                avg_rtt=avg,
            )
            for index, data in buckets.items():
                count = int(data["packets"])
                await _upsert_bucket(
                    run_id=run_id,
                    case_id=case_id,
                    bucket_index=index,
                    packets=count,
                    acked=int(data["acked"]),
                    nacked=int(data["nacked"]),
                    avg_rtt=(
                        round(data["rtt"] / count, 2) if count else None
                    ),
                )
            current = await fetch_case(case_id)
            if current is not None:
                await _broadcast(state, protocol.case_progress(serialize_case(current)))
            last_flush = now
        if now - last_progress_emit >= 1.0:
            current = await fetch_case(case_id)
            if current is not None:
                await _broadcast(state, protocol.case_progress(serialize_case(current)))
            last_progress_emit = now

        await asyncio.sleep(interval)

    avg_rtt = round(rtt_sum / sent, 2) if sent else None
    await _flush_case_progress(
        case_id=case_id, sent=sent, acked=acked, nacked=nacked, avg_rtt=avg_rtt
    )
    for index, data in buckets.items():
        count = int(data["packets"])
        await _upsert_bucket(
            run_id=run_id,
            case_id=case_id,
            bucket_index=index,
            packets=count,
            acked=int(data["acked"]),
            nacked=int(data["nacked"]),
            avg_rtt=(round(data["rtt"] / count, 2) if count else None),
        )
    finished = await _finish_case(
        case_id=case_id,
        run_id=run_id,
        status="passed" if outcome == "passed" else "failed",
        sent=sent,
        acked=acked,
        nacked=nacked,
        avg_rtt=avg_rtt,
        started_perf=started_perf,
        fault_start=window.start_seq if window else None,
        fault_end=window.end_seq if window else None,
        error=None if outcome == "passed" else "ECU frame burst not acknowledged",
    )
    updated_run = await _update_run_counters(run_id)
    await insert_run_event(
        run_id,
        "case_finished",
        {"case_id": case_id, "status": finished["status"]},
    )
    await _broadcast(state, protocol.case_finished(finished))

    if finished["status"] == "failed":
        paused_run = await _set_run_status(run_id, "paused")
        await insert_run_event(
            run_id, "run_paused", {"case_id": case_id, "reason": "case_failed"}
        )
        await _broadcast(state, protocol.run_paused(paused_run, finished))
    else:
        _ = updated_run


async def heartbeat_loop(state: RunState) -> None:
    try:
        while True:
            await asyncio.sleep(WS_HEARTBEAT_S)
            if not state.subscribers:
                continue
            await _broadcast(state, protocol.ping())
    except asyncio.CancelledError:
        pass


async def replay_recent(run_id: int, limit: int = PACKET_RING_BUFFER) -> list[dict]:
    state = await get_state(run_id)
    if state.ring:
        return list(state.ring)[-limit:]
    rows = await fetch_recent_packets(run_id, limit)
    frames = []
    for row in rows:
        frames.append(
            {
                "type": "packet",
                "run_id": int(row["run_id"]),
                "case_id": int(row["case_id"]),
                "seq": int(row["seq"]),
                "payload_hex": str(row["payload_hex"]),
                "ack": bool(int(row["ack"])),
                "rtt_ms": float(row["rtt_ms"]),
                "sent_at": row["sent_at"],
            }
        )
    return frames
