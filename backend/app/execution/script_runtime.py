"""Process manager for the real CAN/UDS scripts.

Unlike the simulated :mod:`app.execution.engine`, this module launches the
actual Python scripts in ``TTL_CANoe/`` as child processes and streams their
output to connected dashboards. It supports:

* a single **trace** process per run (``trace_window.py``), started/stopped
  independently of the test cases;
* one **case** process per test case, each started/paused/resumed/stopped on
  its own without affecting the trace or the other cases;
* a **test connection** probe that opens and closes the bus with the supplied
  Vector configuration.

Output frames are tagged by scope (``trace`` / ``case``) so the UI can route
the live feed and the process-status terminal separately. Case exit codes are
written back to ``test_run_cases`` so the report page keeps working.

Pause/resume use ``psutil`` to suspend the OS process; if ``psutil`` is not
installed the feature degrades to a clear error instead of crashing.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:  # optional, only needed for pause/resume
    import psutil
except Exception:  # pragma: no cover - psutil is optional
    psutil = None  # type: ignore[assignment]

from app.prisma_client import db


# Repo-root/TTL_CANoe (this file lives at backend/app/execution/script_runtime.py)
SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "TTL_CANoe"

# How many recent frames to keep per run for replay when a dashboard connects.
RING_SIZE = 500
# Bounded per-subscriber queue; full queues drop output frames (never status).
QUEUE_SIZE = 2000


# Map a test case (by its normalised name) to the script that runs it. New
# UDS scripts slot in here once they read their Vector config from can_env.
SCRIPT_BY_NAME: dict[str, str] = {
    "find all uds interfaces": "diagnostic_id_scanner.py",
}


def script_for_case_name(name: str | None) -> str | None:
    if not name:
        return None
    return SCRIPT_BY_NAME.get(name.strip().lower())


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ManagedProcess:
    run_id: int
    scope: str  # "trace" | "case"
    label: str
    popen: subprocess.Popen
    case_id: Optional[int] = None
    state: str = "running"  # running | paused | exited | error
    exit_code: Optional[int] = None
    reader: Optional[threading.Thread] = None


@dataclass
class RunChannel:
    run_id: int
    subscribers: set[asyncio.Queue] = field(default_factory=set)
    ring: deque = field(default_factory=lambda: deque(maxlen=RING_SIZE))
    trace: Optional[ManagedProcess] = None
    cases: dict[int, ManagedProcess] = field(default_factory=dict)


class ScriptProcessManager:
    def __init__(self) -> None:
        self._runs: dict[int, RunChannel] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ----- channel / subscriber plumbing ---------------------------------

    def _channel(self, run_id: int) -> RunChannel:
        channel = self._runs.get(run_id)
        if channel is None:
            channel = RunChannel(run_id=run_id)
            self._runs[run_id] = channel
        return channel

    def subscribe(self, run_id: int) -> asyncio.Queue:
        self._loop = asyncio.get_running_loop()
        channel = self._channel(run_id)
        queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_SIZE)
        # Prime the subscriber with current status + recent output.
        queue.put_nowait({"type": "hello", "run_id": run_id})
        for frame in self._status_frames(channel):
            queue.put_nowait(frame)
        for frame in list(channel.ring):
            try:
                queue.put_nowait(frame)
            except asyncio.QueueFull:
                break
        channel.subscribers.add(queue)
        return queue

    def unsubscribe(self, run_id: int, queue: asyncio.Queue) -> None:
        channel = self._runs.get(run_id)
        if channel is not None:
            channel.subscribers.discard(queue)

    def _status_frames(self, channel: RunChannel) -> list[dict[str, Any]]:
        frames: list[dict[str, Any]] = []
        if channel.trace is not None:
            frames.append(self._status_frame(channel.trace))
        for proc in channel.cases.values():
            frames.append(self._status_frame(proc))
        return frames

    def _status_frame(self, proc: ManagedProcess) -> dict[str, Any]:
        return {
            "type": "status",
            "scope": proc.scope,
            "case_id": proc.case_id,
            "label": proc.label,
            "state": proc.state,
            "exit_code": proc.exit_code,
            "ts": _iso_now(),
        }

    def _emit(self, run_id: int, frame: dict[str, Any]) -> None:
        """Deliver a frame to all subscribers. Safe to call on the loop thread."""
        channel = self._runs.get(run_id)
        if channel is None:
            return
        if frame.get("type") != "status":
            channel.ring.append(frame)
        dead: list[asyncio.Queue] = []
        for queue in list(channel.subscribers):
            try:
                queue.put_nowait(frame)
            except asyncio.QueueFull:
                if frame.get("type") == "status":
                    # Status must be delivered; make room by dropping oldest.
                    try:
                        queue.get_nowait()
                        queue.put_nowait(frame)
                    except Exception:
                        dead.append(queue)
            except Exception:
                dead.append(queue)
        for queue in dead:
            channel.subscribers.discard(queue)

    def _emit_threadsafe(self, run_id: int, frame: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            return
        loop.call_soon_threadsafe(self._emit, run_id, frame)

    # ----- process launching --------------------------------------------

    def _spawn(
        self,
        *,
        run_id: int,
        scope: str,
        label: str,
        script: str,
        env_overrides: dict[str, str],
        case_id: Optional[int] = None,
    ) -> ManagedProcess:
        script_path = SCRIPTS_DIR / script
        if not script_path.is_file():
            raise FileNotFoundError(f"Script not found: {script}")

        env = os.environ.copy()
        env.update(env_overrides)
        env["PYTHONUNBUFFERED"] = "1"

        popen = subprocess.Popen(
            [sys.executable, "-u", str(script_path)],
            cwd=str(SCRIPTS_DIR),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        proc = ManagedProcess(
            run_id=run_id,
            scope=scope,
            label=label,
            popen=popen,
            case_id=case_id,
        )
        reader = threading.Thread(
            target=self._read_output, args=(proc,), daemon=True
        )
        proc.reader = reader
        reader.start()
        self._emit(run_id, self._status_frame(proc))
        self._emit(
            run_id,
            {
                "type": "output",
                "scope": scope,
                "case_id": case_id,
                "line": f"[started] {label} ({script})",
                "ts": _iso_now(),
            },
        )
        return proc

    def _read_output(self, proc: ManagedProcess) -> None:
        stdout = proc.popen.stdout
        try:
            if stdout is not None:
                for line in stdout:
                    self._emit_threadsafe(
                        proc.run_id,
                        {
                            "type": "output",
                            "scope": proc.scope,
                            "case_id": proc.case_id,
                            "line": line.rstrip("\n"),
                            "ts": _iso_now(),
                        },
                    )
        except Exception:
            pass
        finally:
            code = proc.popen.wait()
            proc.exit_code = code
            if proc.state != "error":
                proc.state = "exited"
            self._emit_threadsafe(proc.run_id, self._status_frame(proc))
            self._emit_threadsafe(
                proc.run_id,
                {
                    "type": "output",
                    "scope": proc.scope,
                    "case_id": proc.case_id,
                    "line": f"[exited] {proc.label} (code {code})",
                    "ts": _iso_now(),
                },
            )
            if proc.scope == "case" and proc.case_id is not None:
                self._schedule(self._finish_case(proc.case_id, code))

    def _schedule(self, coro) -> None:
        loop = self._loop
        if loop is not None:
            asyncio.run_coroutine_threadsafe(coro, loop)

    # ----- DB write-backs for cases -------------------------------------

    async def _mark_case_running(self, case_id: int) -> None:
        await db.execute_raw(
            "UPDATE `test_run_cases` SET `status` = 'running', "
            "`attempt` = `attempt` + 1, `started_at` = UTC_TIMESTAMP(6), "
            "`finished_at` = NULL, `duration_ms` = NULL, `error` = NULL "
            "WHERE `id` = ?",
            case_id,
        )

    async def _finish_case(self, case_id: int, exit_code: int) -> None:
        status = "passed" if exit_code == 0 else "failed"
        error = None if exit_code == 0 else f"Script exited with code {exit_code}"
        await db.execute_raw(
            "UPDATE `test_run_cases` SET `status` = ?, "
            "`finished_at` = UTC_TIMESTAMP(6), "
            "`duration_ms` = CASE WHEN `started_at` IS NULL THEN NULL ELSE "
            "TIMESTAMPDIFF(MICROSECOND, `started_at`, UTC_TIMESTAMP(6)) / 1000 END, "
            "`error` = ? WHERE `id` = ?",
            status,
            error,
            case_id,
        )

    async def _mark_case_stopped(self, case_id: int) -> None:
        await db.execute_raw(
            "UPDATE `test_run_cases` SET `status` = 'skipped', "
            "`finished_at` = UTC_TIMESTAMP(6), `error` = 'stopped by user' "
            "WHERE `id` = ? AND `status` = 'running'",
            case_id,
        )

    # ----- public API (called from the router) --------------------------

    async def start_trace(self, run_id: int, env_overrides: dict[str, str]) -> None:
        self._loop = asyncio.get_running_loop()
        channel = self._channel(run_id)
        if channel.trace is not None and channel.trace.popen.poll() is None:
            raise RuntimeError("Trace is already running")
        channel.trace = self._spawn(
            run_id=run_id,
            scope="trace",
            label="Trace window",
            script="trace_window.py",
            env_overrides=env_overrides,
        )

    async def stop_trace(self, run_id: int) -> None:
        channel = self._channel(run_id)
        if channel.trace is None or channel.trace.popen.poll() is not None:
            raise RuntimeError("Trace is not running")
        await asyncio.to_thread(self._terminate, channel.trace)

    async def start_case(
        self,
        run_id: int,
        case_id: int,
        label: str,
        script: str,
        env_overrides: dict[str, str],
    ) -> None:
        self._loop = asyncio.get_running_loop()
        channel = self._channel(run_id)
        existing = channel.cases.get(case_id)
        if existing is not None and existing.popen.poll() is None:
            raise RuntimeError("This test case is already running")
        await self._mark_case_running(case_id)
        channel.cases[case_id] = self._spawn(
            run_id=run_id,
            scope="case",
            label=label,
            script=script,
            env_overrides=env_overrides,
            case_id=case_id,
        )

    async def pause_case(self, run_id: int, case_id: int) -> None:
        proc = self._require_case(run_id, case_id)
        if psutil is None:
            raise RuntimeError("Pause/resume requires psutil on the server")
        await asyncio.to_thread(self._suspend, proc)
        proc.state = "paused"
        self._emit(run_id, self._status_frame(proc))

    async def resume_case(self, run_id: int, case_id: int) -> None:
        proc = self._require_case(run_id, case_id)
        if psutil is None:
            raise RuntimeError("Pause/resume requires psutil on the server")
        await asyncio.to_thread(self._resume, proc)
        proc.state = "running"
        self._emit(run_id, self._status_frame(proc))

    async def stop_case(self, run_id: int, case_id: int) -> None:
        proc = self._require_case(run_id, case_id)
        await asyncio.to_thread(self._terminate, proc)
        await self._mark_case_stopped(case_id)

    def _require_case(self, run_id: int, case_id: int) -> ManagedProcess:
        channel = self._channel(run_id)
        proc = channel.cases.get(case_id)
        if proc is None or proc.popen.poll() is not None:
            raise RuntimeError("This test case is not running")
        return proc

    def shutdown_all(self) -> int:
        """Terminate every live child process. Called on server shutdown so
        trace/case processes don't outlive the backend and keep the bus open."""
        terminated = 0
        for channel in list(self._runs.values()):
            procs = [channel.trace, *channel.cases.values()]
            for proc in procs:
                if proc is not None and proc.popen.poll() is None:
                    try:
                        self._terminate(proc)
                        terminated += 1
                    except Exception:
                        pass
        return terminated

    # ----- OS process control -------------------------------------------

    def _ps_targets(self, proc: ManagedProcess) -> list:
        if psutil is None:
            return []
        try:
            parent = psutil.Process(proc.popen.pid)
        except Exception:
            return []
        targets = [parent]
        try:
            targets.extend(parent.children(recursive=True))
        except Exception:
            pass
        return targets

    def _suspend(self, proc: ManagedProcess) -> None:
        for target in self._ps_targets(proc):
            try:
                target.suspend()
            except Exception:
                pass

    def _resume(self, proc: ManagedProcess) -> None:
        for target in self._ps_targets(proc):
            try:
                target.resume()
            except Exception:
                pass

    def _terminate(self, proc: ManagedProcess) -> None:
        if proc.popen.poll() is not None:
            return
        if psutil is not None:
            targets = self._ps_targets(proc)
            for target in targets:
                try:
                    target.resume()  # a suspended process can't be killed cleanly
                except Exception:
                    pass
                try:
                    target.terminate()
                except Exception:
                    pass
            _, alive = (psutil.wait_procs(targets, timeout=3) if targets else ([], []))
            for target in alive:
                try:
                    target.kill()
                except Exception:
                    pass
        else:
            try:
                proc.popen.terminate()
            except Exception:
                pass
        try:
            proc.popen.wait(timeout=3)
        except Exception:
            try:
                proc.popen.kill()
            except Exception:
                pass


manager = ScriptProcessManager()


def test_connection(env_overrides: dict[str, str]) -> tuple[bool, str]:
    """Open the bus with the supplied config in a short child process."""
    probe = (
        "import can, can_env\n"
        "bus = can.Bus(**can_env.bus_kwargs())\n"
        "bus.shutdown()\n"
        "print('Connection OK')\n"
    )
    env = os.environ.copy()
    env.update(env_overrides)
    try:
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(SCRIPTS_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False, "Connection test timed out after 20s"
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return True, output or "Connection OK"
    return False, output or f"Exited with code {result.returncode}"
