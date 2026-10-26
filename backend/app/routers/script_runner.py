"""Run the allow-listed local scripts and stream their output to the server terminal."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.auth import get_current_user


router = APIRouter(prefix="/scripts", tags=["scripts"])
SCRIPT_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
AVAILABLE_SCRIPTS = {
    "test-1": "send_data_packets.py",
    "test-2": "receive_data_packets.py",
    "send_message": "send_message.py",
    "trace_window": "trace_window.py",
    "dummy": "dummy.py",
}


async def _stream_script(script_id: str, script_path: Path):
    print(f"[scripts] Starting {script_id} ({script_path.name})", flush=True)
    process = subprocess.Popen(
        [
        sys.executable,
        "-u",
        str(script_path),
        ],
        cwd=SCRIPT_DIRECTORY,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    try:
        if process.stdout is None:
            raise RuntimeError("Script stdout pipe was not opened")
        while True:
            line = await asyncio.to_thread(process.stdout.readline)
            if not line:
                break
            print(line, end="", flush=True)
            yield line

        return_code = await asyncio.to_thread(process.wait)
        print(
            f"[scripts] {script_id} exited with code {return_code}",
            flush=True,
        )
        yield f"\n__SCRIPT_EXIT_CODE__={return_code}\n"
    finally:
        if process.poll() is None:
            process.terminate()
            await asyncio.to_thread(process.wait)
        if process.stdout is not None:
            process.stdout.close()


@router.post("/{script_id}/run")
async def run_script(
    script_id: str,
    _current_user=Depends(get_current_user),
):
    filename = AVAILABLE_SCRIPTS.get(script_id)
    if filename is None:
        raise HTTPException(status_code=404, detail="Script not found")

    script_path = SCRIPT_DIRECTORY / filename
    if not script_path.is_file():
        raise HTTPException(status_code=500, detail="Configured script is missing")

    return StreamingResponse(
        _stream_script(script_id, script_path),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
