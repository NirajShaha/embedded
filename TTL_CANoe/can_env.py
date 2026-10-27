"""Runtime configuration helpers for the CAN/UDS scripts.

The scripts in this folder were written to be run by hand with hard-coded
Vector settings. When they are launched by the backend process manager the
same settings are supplied through environment variables so the operator can
change them from the dashboard without editing any script.

Every lookup falls back to the original hard-coded default, so running a
script directly (``python diagnostic_id_scanner.py``) behaves exactly as
before.
"""

from __future__ import annotations

import os


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "y", "on")


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw, 0)
    except (TypeError, ValueError):
        return default


def channel() -> object:
    """Vector channels are integers; other interfaces may use a string."""
    raw = os.environ.get("CAN_CHANNEL")
    if raw is None or raw == "":
        return 0
    try:
        return int(raw, 0)
    except (TypeError, ValueError):
        return raw


def bus_kwargs() -> dict:
    """Keyword arguments for ``can.Bus`` built from the environment."""
    return {
        "interface": os.environ.get("CAN_INTERFACE", "vector"),
        "channel": channel(),
        "app_name": os.environ.get("CAN_APP_NAME", "Python"),
        "fd": _bool("CAN_FD", True),
        "bitrate": _int("CAN_BITRATE", 500000),
        "dbitrate": _int("CAN_DBITRATE", 2000000),
        "receive_own_messages": _bool("CAN_RX_OWN", True),
    }


def source_id(default: int = 0x471) -> int:
    return _int("UDS_SOURCE_ID", default)


def destination_id(default: int = 0x479) -> int:
    return _int("UDS_DEST_ID", default)


def scan_start(default: int = 0x400) -> int:
    return _int("UDS_SCAN_START", default)


def scan_end(default: int = 0x500) -> int:
    return _int("UDS_SCAN_END", default)


def request_bytes(default: str = "02 10 03 00 00 00 00 00") -> list:
    """Parse the manual message / request payload into a list of byte ints."""
    raw = os.environ.get("UDS_MANUAL_MSG") or os.environ.get("UDS_REQUEST") or default
    tokens = raw.replace(",", " ").split()
    out = []
    for token in tokens:
        try:
            out.append(int(token, 16) & 0xFF)
        except ValueError:
            continue
    return out or [0x02, 0x10, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00]
