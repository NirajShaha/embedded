"""Test-run execution API: create, inspect, resume, retry, cancel + report."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketDisconnect

from app.auth import get_current_user
from app.execution import engine, protocol
from app.execution.settings import (
    DEFAULT_CASE_DURATION_S,
    MAX_CASES_PER_RUN,
    MAX_CASE_DURATION_S,
    MIN_CASE_DURATION_S,
    PACKET_RING_BUFFER,
)
from app.execution.store import (
    build_summary,
    fetch_case,
    fetch_case_buckets,
    fetch_recent_packets,
    fetch_run,
    fetch_run_cases,
    fetch_run_events,
    insert_run_event,
    serialize_case,
    serialize_run,
)
from app.prisma_client import db
from app.routers.test_cases import TEST_CASE_INCLUDE, _normalize_test_case_ids
from app.test_case_overrides import map_test_case


router = APIRouter(prefix="/executions", tags=["executions"])


class CreateRunPayload(BaseModel):
    project_id: int = Field(gt=0)
    test_case_ids: list[int] = Field(min_length=1)
    duration_per_case_s: float = Field(default=DEFAULT_CASE_DURATION_S)
    packet_loss_rate: float = Field(default=0.02, ge=0.0, le=1.0)


def _resolve_duration(value: float) -> float:
    return min(MAX_CASE_DURATION_S, max(MIN_CASE_DURATION_S, float(value)))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_run(payload: CreateRunPayload, current_user=Depends(get_current_user)):
    project = await db.projects.find_unique(where={"id": payload.project_id})
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    test_case_ids = _normalize_test_case_ids(payload.test_case_ids)
    if not test_case_ids:
        raise HTTPException(status_code=400, detail="No valid test cases selected")
    if len(test_case_ids) > MAX_CASES_PER_RUN:
        raise HTTPException(
            status_code=400,
            detail=f"A run supports at most {MAX_CASES_PER_RUN} test cases",
        )

    rows = await db.test_cases.find_many(
        where={"id": {"in": test_case_ids}, "deleted_at": None},
        include=TEST_CASE_INCLUDE,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No test cases found")
    found_ids = {int(row.id) for row in rows}
    missing = sorted(set(test_case_ids) - found_ids)
    if missing:
        raise HTTPException(
            status_code=409,
            detail="One or more selected test cases are no longer available",
        )
    by_id = {int(row.id): row for row in rows}
    ordered = [by_id[case_id] for case_id in test_case_ids]

    duration_s = _resolve_duration(payload.duration_per_case_s)
    planned = engine.packets_per_case(duration_s)

    run_id_rows: list[dict] = await db.query_raw(
        "INSERT INTO `test_runs` (`project_id`, `status`, `total_cases`, "
        "`current_position`, `duration_per_case_s`, `packet_loss_rate`, "
        "`started_at`, `created_by`) VALUES (?, 'running', ?, ?, ?, ?, "
        "UTC_TIMESTAMP(6), ?)",
        payload.project_id,
        len(ordered),
        1,
        duration_s,
        float(payload.packet_loss_rate),
        int(current_user.id),
    )
    created: list[dict] = await db.query_raw("SELECT LAST_INSERT_ID() AS id")
    run_id = int(created[0]["id"] if isinstance(created[0], dict) else created[0][0])
    _ = run_id_rows

    for position, row in enumerate(ordered, start=1):
        mapped = map_test_case(row)
        label = str(
            mapped.get("test_case_name")
            or mapped.get("action_test_case")
            or f"Test case {mapped['id']}"
        )[:500]
        await db.execute_raw(
            "INSERT INTO `test_run_cases` (`run_id`, `position`, `test_case_id`, "
            "`test_case_name`, `status`, `packets_planned`) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            run_id,
            position,
            int(row.id),
            label,
            planned,
        )

    await insert_run_event(
        run_id,
        "run_created",
        {
            "project_id": payload.project_id,
            "total_cases": len(ordered),
            "duration_per_case_s": duration_s,
        },
    )
    run = await fetch_run(run_id)
    assert run is not None
    cases = await fetch_run_cases(run_id)
    await engine.start_worker(run_id)
    return {
        "run": serialize_run(run),
        "cases": [serialize_case(case) for case in cases],
    }


@router.get("/{run_id}")
async def get_run(run_id: int, _user=Depends(get_current_user)):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    cases = await fetch_run_cases(run_id)
    return {
        "run": serialize_run(run),
        "cases": [serialize_case(case) for case in cases],
    }


@router.get("/{run_id}/report")
async def get_run_report(run_id: int, _user=Depends(get_current_user)):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    cases = await fetch_run_cases(run_id)
    serialized_run = serialize_run(run)
    serialized_cases = [serialize_case(case) for case in cases]
    return {
        "run": serialized_run,
        "cases": serialized_cases,
        "summary": build_summary(serialized_run, serialized_cases),
        "buckets": await fetch_case_buckets(run_id),
        "events": await fetch_run_events(run_id),
    }


@router.get("")
async def list_runs(
    project_id: int = Query(gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    _user=Depends(get_current_user),
):
    rows: list[dict] = await db.query_raw(
        "SELECT * FROM `test_runs` WHERE `project_id` = ? "
        "ORDER BY `id` DESC LIMIT ?",
        project_id,
        limit,
    )
    return [serialize_run(dict(row)) for row in rows]


@router.post("/{run_id}/resume")
async def resume_run(run_id: int, _user=Depends(get_current_user)):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if str(run["status"]) not in {"paused", "running"}:
        raise HTTPException(
            status_code=409,
            detail=f"Run is {run['status']} and cannot be resumed",
        )
    cases = await fetch_run_cases(run_id)
    remaining = [
        case for case in cases if str(case["status"]) in {"pending", "running"}
    ]
    failed = [case for case in cases if str(case["status"]) == "failed"]
    if failed:
        raise HTTPException(
            status_code=409,
            detail="Run is paused on a failed case — retry the failed case first",
        )
    if not remaining:
        raise HTTPException(status_code=409, detail="Run has no remaining cases")
    for case in remaining:
        if str(case["status"]) == "running":
            await db.execute_raw(
                "UPDATE `test_run_cases` SET `status` = 'pending', "
                "`started_at` = NULL WHERE `id` = ?",
                int(case["id"]),
            )
    await db.execute_raw(
        "UPDATE `test_runs` SET `status` = 'running', `finished_at` = NULL, "
        "`updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
        run_id,
    )
    await insert_run_event(run_id, "run_resumed", {})
    await engine.request_stop(run_id)
    await asyncio.sleep(0.1)
    await engine.start_worker(run_id)
    updated = await fetch_run(run_id)
    assert updated is not None
    return {"run": serialize_run(updated)}


@router.post("/{run_id}/retry")
async def retry_failed_case(
    run_id: int,
    from_position: int | None = Query(default=None, ge=1),
    _user=Depends(get_current_user),
):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if str(run["status"]) not in {"paused", "failed"}:
        raise HTTPException(
            status_code=409,
            detail=f"Run is {run['status']} — nothing to retry",
        )
    cases = await fetch_run_cases(run_id)
    if from_position is not None:
        target = next(
            (case for case in cases if int(case["position"]) == from_position), None
        )
        if target is None or str(target["status"]) != "failed":
            raise HTTPException(
                status_code=409, detail="That position is not a failed case"
            )
    else:
        target = next(
            (case for case in cases if str(case["status"]) == "failed"), None
        )
        if target is None:
            raise HTTPException(status_code=409, detail="Run has no failed case")
    await db.execute_raw(
        "UPDATE `test_run_cases` SET `status` = 'pending', `started_at` = NULL, "
        "`finished_at` = NULL, `error` = NULL WHERE `id` = ?",
        int(target["id"]),
    )
    await db.execute_raw(
        "UPDATE `test_runs` SET `status` = 'running', `finished_at` = NULL, "
        "`current_position` = ?, `updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
        int(target["position"]),
        run_id,
    )
    await insert_run_event(
        run_id,
        "case_retried",
        {"case_id": int(target["id"]), "position": int(target["position"])},
    )
    await engine.request_stop(run_id)
    await asyncio.sleep(0.1)
    await engine.start_worker(run_id)
    updated = await fetch_run(run_id)
    assert updated is not None
    retried = await fetch_case(int(target["id"]))
    assert retried is not None
    return {"run": serialize_run(updated), "case": serialize_case(retried)}


@router.post("/{run_id}/skip")
async def skip_failed_case(
    run_id: int,
    from_position: int | None = Query(default=None, ge=1),
    _user=Depends(get_current_user),
):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if str(run["status"]) not in {"paused", "failed", "running"}:
        raise HTTPException(
            status_code=409, detail=f"Run is {run['status']} — nothing to skip"
        )
    cases = await fetch_run_cases(run_id)
    if from_position is not None:
        target = next(
            (case for case in cases if int(case["position"]) == from_position), None
        )
        if target is None or str(target["status"]) != "failed":
            raise HTTPException(
                status_code=409, detail="That position is not a failed case"
            )
    else:
        target = next(
            (case for case in cases if str(case["status"]) == "failed"), None
        )
        if target is None:
            raise HTTPException(status_code=409, detail="Run has no failed case")
    await db.execute_raw(
        "UPDATE `test_run_cases` SET `status` = 'skipped', `error` = 'skipped by user' "
        "WHERE `id` = ?",
        int(target["id"]),
    )
    remaining = [
        case
        for case in await fetch_run_cases(run_id)
        if str(case["status"]) in {"pending", "running"}
    ]
    if not remaining:
        failed_count = sum(
            1
            for case in await fetch_run_cases(run_id)
            if str(case["status"]) == "failed"
        )
        final_status = "failed" if failed_count else "completed"
        await db.execute_raw(
            "UPDATE `test_runs` SET `status` = ?, `finished_at` = UTC_TIMESTAMP(6), "
            "`updated_at` = UTC_TIMESTAMP(6) WHERE `id` = ?",
            final_status,
            run_id,
        )
    else:
        await db.execute_raw(
            "UPDATE `test_runs` SET `status` = 'running', `finished_at` = NULL, "
            "`current_position` = ?, `updated_at` = UTC_TIMESTAMP(6) "
            "WHERE `id` = ?",
            int(min(int(case["position"]) for case in remaining)),
            run_id,
        )
    await insert_run_event(
        run_id,
        "case_skipped",
        {"case_id": int(target["id"]), "position": int(target["position"])},
    )
    await engine.request_stop(run_id)
    await asyncio.sleep(0.1)
    updated_run = await fetch_run(run_id)
    assert updated_run is not None
    if str(updated_run["status"]) == "running":
        await engine.start_worker(run_id)
    else:
        from app.execution.store import build_summary as _summary

        cases_now = await fetch_run_cases(run_id)
        serialized = [serialize_case(case) for case in cases_now]
        summary = _summary(serialize_run(updated_run), serialized)
        state = await engine.get_state(run_id)
        await engine._broadcast(
            state, protocol.run_finished(serialize_run(updated_run), summary)
        )
    updated = await fetch_run(run_id)
    assert updated is not None
    return {"run": serialize_run(updated)}


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: int, _user=Depends(get_current_user)):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if str(run["status"]) in {"completed", "failed", "cancelled"}:
        raise HTTPException(
            status_code=409, detail=f"Run is already {run['status']}"
        )
    await engine.request_stop(run_id)
    await db.execute_raw(
        "UPDATE `test_run_cases` SET `status` = 'skipped' "
        "WHERE `run_id` = ? AND `status` IN ('pending', 'running')",
        run_id,
    )
    await db.execute_raw(
        "UPDATE `test_runs` SET `status` = 'cancelled', "
        "`finished_at` = UTC_TIMESTAMP(6), `updated_at` = UTC_TIMESTAMP(6) "
        "WHERE `id` = ?",
        run_id,
    )
    await insert_run_event(run_id, "run_cancelled", {})
    state = await engine.get_state(run_id)
    updated = await fetch_run(run_id)
    assert updated is not None
    serialized = serialize_run(updated)
    await engine._broadcast(state, protocol.run_cancelled(serialized))
    return {"run": serialized}


@router.get("/{run_id}/packets")
async def get_packets(
    run_id: int,
    limit: int = Query(default=200, ge=1, le=1000),
    _user=Depends(get_current_user),
):
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "packets": await fetch_recent_packets(run_id, limit)}


async def _authenticate_socket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        auth = websocket.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    if not token:
        return None
    import jwt

    from app.config import settings
    from app.prisma_client import db as prisma_db

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    return await prisma_db.users.find_unique(where={"id": user_id})


@router.websocket("/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: int):
    await websocket.accept()
    user = await _authenticate_socket(websocket)
    if user is None:
        await websocket.close(code=4401)
        return
    run = await fetch_run(run_id)
    if run is None:
        await websocket.close(code=4404)
        return
    state, sub = await engine.subscribe(run_id)
    disconnected = asyncio.Event()

    async def _reader() -> None:
        try:
            while True:
                incoming = await websocket.receive_text()
                text = incoming.strip()
                is_ping = text.lower() in {"ping", "pong"}
                if not is_ping and text:
                    try:
                        payload = json.loads(text)
                    except Exception:
                        payload = None
                    is_ping = isinstance(payload, dict) and payload.get("type") in {
                        "ping",
                        "pong",
                    }
                if is_ping:
                    try:
                        await websocket.send_json(protocol.ping())
                    except Exception:
                        break
        except Exception:
            pass
        finally:
            disconnected.set()

    reader = asyncio.ensure_future(_reader())
    try:
        try:
            serialized_run, serialized_cases = await engine.snapshot_payload(run_id)
            await websocket.send_json(protocol.hello(run_id, resume=True))
            await websocket.send_json(
                protocol.snapshot(serialized_run, serialized_cases)
            )
            replay = await engine.replay_recent(run_id, PACKET_RING_BUFFER)
            if replay:
                await websocket.send_json(protocol.replay(replay))
        except (WebSocketDisconnect, RuntimeError):
            return
        while True:
            get_task = asyncio.ensure_future(sub.queue.get())
            disc_task = asyncio.ensure_future(disconnected.wait())
            done, pending = await asyncio.wait(
                {get_task, disc_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            if disc_task in done:
                break
            try:
                message = get_task.result()
            except Exception:
                break
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                break
            except Exception:
                break
    finally:
        reader.cancel()
        disconnected.set()
        engine.unsubscribe(state, sub)
        try:
            await websocket.close()
        except Exception:
            pass
