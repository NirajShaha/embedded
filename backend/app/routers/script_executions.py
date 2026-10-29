"""REST + WebSocket API for running the real CAN/UDS scripts from a run.

This complements :mod:`app.routers.executions` (the simulated engine). A
"script run" reuses the ``test_runs`` / ``test_run_cases`` tables so the report
page keeps working, but nothing starts automatically: the operator drives the
trace window and each test case by hand from the dashboard.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketDisconnect

from app.auth import get_current_user
from app.execution.script_runtime import (
    manager,
    script_for_case_name,
    test_connection,
)
from app.execution.settings import MAX_CASES_PER_RUN
from app.execution.store import (
    fetch_case,
    fetch_run,
    fetch_run_cases,
    insert_run_event,
    serialize_case,
    serialize_run,
)
from app.prisma_client import db
from app.routers.executions import _authenticate_socket
from app.routers.test_cases import _normalize_test_case_ids


router = APIRouter(prefix="/executions", tags=["script-executions"])


class VectorConfig(BaseModel):
    interface: str = "vector"
    channel: int = 0
    app_name: str = "Python"
    fd: bool = True
    bitrate: int = 500000
    dbitrate: int = 2000000
    receive_own_messages: bool = True


class CreateScriptRunPayload(BaseModel):
    project_id: int = Field(gt=0)
    test_case_ids: list[int] = Field(min_length=1)


class CaseStartPayload(BaseModel):
    config: VectorConfig = Field(default_factory=VectorConfig)
    source_id: str | None = None
    destination_id: str | None = None
    manual_message: str | None = None


def _vector_env(config: VectorConfig) -> dict[str, str]:
    return {
        "CAN_INTERFACE": config.interface,
        "CAN_CHANNEL": str(config.channel),
        "CAN_APP_NAME": config.app_name,
        "CAN_FD": "1" if config.fd else "0",
        "CAN_BITRATE": str(config.bitrate),
        "CAN_DBITRATE": str(config.dbitrate),
        "CAN_RX_OWN": "1" if config.receive_own_messages else "0",
    }


def _parse_can_id(raw: str | None) -> int | None:
    if raw is None:
        return None
    text = raw.strip().lower().removeprefix("0x").removesuffix("h")
    if not text:
        return None
    try:
        return int(text, 16)
    except ValueError:
        return None


async def _require_run(run_id: int) -> dict:
    run = await fetch_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/script-runs", status_code=status.HTTP_201_CREATED)
async def create_script_run(
    payload: CreateScriptRunPayload, current_user=Depends(get_current_user)
):
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

    placeholders = ",".join(["?"] * len(test_case_ids))
    rows: list[dict] = await db.query_raw(
        "SELECT `id`, `action_test_case` FROM `test_cases` "
        f"WHERE `id` IN ({placeholders}) AND `deleted_at` IS NULL",
        *test_case_ids,
    )
    by_id = {int(row["id"]): row for row in rows}
    ordered_ids = [cid for cid in test_case_ids if cid in by_id]
    if not ordered_ids:
        raise HTTPException(status_code=404, detail="No test cases found")

    run_rows: list[dict] = await db.query_raw(
        "INSERT INTO `test_runs` (`project_id`, `status`, `total_cases`, "
        "`current_position`, `started_at`, `created_by`) "
        "VALUES (?, 'running', ?, ?, UTC_TIMESTAMP(6), ?)",
        payload.project_id,
        len(ordered_ids),
        1,
        int(current_user.id),
    )
    _ = run_rows
    created: list[dict] = await db.query_raw("SELECT LAST_INSERT_ID() AS id")
    run_id = int(created[0]["id"] if isinstance(created[0], dict) else created[0][0])

    for position, cid in enumerate(ordered_ids, start=1):
        label = str(by_id[cid].get("action_test_case") or f"Test case {cid}")[:500]
        await db.execute_raw(
            "INSERT INTO `test_run_cases` (`run_id`, `position`, `test_case_id`, "
            "`test_case_name`, `status`, `packets_planned`) "
            "VALUES (?, ?, ?, ?, 'pending', 0)",
            run_id,
            position,
            cid,
            label,
        )

    await insert_run_event(
        run_id,
        "script_run_created",
        {"project_id": payload.project_id, "total_cases": len(ordered_ids)},
    )
    run = await fetch_run(run_id)
    assert run is not None
    cases = await fetch_run_cases(run_id)
    return {
        "run": serialize_run(run),
        "cases": [serialize_case(case) for case in cases],
    }


@router.post("/{run_id}/test-connection")
async def run_test_connection(
    run_id: int, config: VectorConfig, _user=Depends(get_current_user)
):
    await _require_run(run_id)
    ok, message = await asyncio.to_thread(test_connection, _vector_env(config))
    return {"ok": ok, "message": message}


@router.post("/{run_id}/trace/start")
async def start_trace(
    run_id: int, config: VectorConfig, _user=Depends(get_current_user)
):
    await _require_run(run_id)
    try:
        await manager.start_trace(run_id, _vector_env(config))
    except (RuntimeError, FileNotFoundError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    return {"ok": True}


@router.post("/{run_id}/trace/stop")
async def stop_trace(run_id: int, _user=Depends(get_current_user)):
    await _require_run(run_id)
    try:
        await manager.stop_trace(run_id)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return {"ok": True}


@router.post("/{run_id}/cases/{case_id}/start")
async def start_case(
    run_id: int,
    case_id: int,
    payload: CaseStartPayload,
    _user=Depends(get_current_user),
):
    await _require_run(run_id)
    case = await fetch_case(case_id)
    if case is None or int(case["run_id"]) != run_id:
        raise HTTPException(status_code=404, detail="Case not found for this run")

    name = case.get("test_case_name")
    script = script_for_case_name(name)
    if script is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f'No script is wired for "{name}" yet. '
                '"Find all UDS interfaces" is supported.'
            ),
        )

    env = _vector_env(payload.config)
    source = _parse_can_id(payload.source_id)
    destination = _parse_can_id(payload.destination_id)
    if source is not None:
        env["UDS_SOURCE_ID"] = f"0x{source:X}"
        env["UDS_SCAN_START"] = f"0x{source:X}"
    if destination is not None:
        env["UDS_DEST_ID"] = f"0x{destination:X}"
        env["UDS_SCAN_END"] = f"0x{destination:X}"
    if payload.manual_message and payload.manual_message.strip():
        env["UDS_MANUAL_MSG"] = payload.manual_message.strip()

    try:
        await manager.start_case(
            run_id, case_id, str(name or f"Case {case_id}"), script, env
        )
    except (RuntimeError, FileNotFoundError) as error:
        raise HTTPException(status_code=409, detail=str(error))
    refreshed = await fetch_case(case_id)
    assert refreshed is not None
    return {"case": serialize_case(refreshed)}


@router.post("/{run_id}/cases/{case_id}/pause")
async def pause_case(run_id: int, case_id: int, _user=Depends(get_current_user)):
    await _require_run(run_id)
    try:
        await manager.pause_case(run_id, case_id)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return {"ok": True}


@router.post("/{run_id}/cases/{case_id}/resume")
async def resume_case(run_id: int, case_id: int, _user=Depends(get_current_user)):
    await _require_run(run_id)
    try:
        await manager.resume_case(run_id, case_id)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error))
    return {"ok": True}


@router.post("/{run_id}/cases/{case_id}/stop")
async def stop_case(run_id: int, case_id: int, _user=Depends(get_current_user)):
    await _require_run(run_id)
    try:
        await manager.stop_case(run_id, case_id)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error))
    refreshed = await fetch_case(case_id)
    return {"case": serialize_case(refreshed) if refreshed else None}


@router.websocket("/{run_id}/script-stream")
async def script_stream(websocket: WebSocket, run_id: int):
    await websocket.accept()
    user = await _authenticate_socket(websocket)
    if user is None:
        await websocket.close(code=4401)
        return
    run = await fetch_run(run_id)
    if run is None:
        await websocket.close(code=4404)
        return

    queue = manager.subscribe(run_id)
    disconnected = asyncio.Event()

    async def _reader() -> None:
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            pass
        finally:
            disconnected.set()

    reader = asyncio.ensure_future(_reader())
    try:
        # Send the current case snapshot so the UI can render checkboxes/status.
        cases = await fetch_run_cases(run_id)
        await websocket.send_json(
            {
                "type": "snapshot",
                "run": serialize_run(run),
                "cases": [serialize_case(case) for case in cases],
            }
        )
        while True:
            get_task = asyncio.ensure_future(queue.get())
            disc_task = asyncio.ensure_future(disconnected.wait())
            done, pending = await asyncio.wait(
                {get_task, disc_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            if disc_task in done:
                break
            try:
                frame = get_task.result()
            except Exception:
                break
            try:
                await websocket.send_json(frame)
            except (WebSocketDisconnect, RuntimeError):
                break
    finally:
        reader.cancel()
        disconnected.set()
        manager.unsubscribe(run_id, queue)
        try:
            await websocket.close()
        except Exception:
            pass
