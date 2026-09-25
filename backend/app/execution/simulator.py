"""Deterministic simulated ECU packet generator.

Each test case behaves like a Python harness on the bench: it transmits a
stream of binary frames and records whether every single frame was
acknowledged by the ECU. Long-running faults are modelled as *segments* — a
failing case goes quiet (NACK storm) for one contiguous window instead of
sprinkling random losses, which is what real CAN/LIN failures look like and
what the charts need to visualise.

The generator is seeded per (run_id, test_case_id, attempt) so a retry of the
same failed case produces a *different* stream (the fault window comes from
the attempt seed), while replays of a completed attempt are bit-identical.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from app.execution.settings import (
    DEFAULT_PACKET_LOSS_RATE,
    PACKET_BYTES,
)


@dataclass(frozen=True)
class PacketSpec:
    seq: int
    payload: bytes
    ack: bool
    rtt_ms: float


@dataclass(frozen=True)
class FaultWindow:
    start_seq: int
    end_seq: int


def derive_seed(run_id: int, test_case_id: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"ecu-run:{run_id}:case:{test_case_id}:attempt:{attempt}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big")


def choose_outcome(
    test_case_id: int,
    packet_count: int,
    packet_loss_rate: float,
    rng: random.Random,
) -> tuple[str, FaultWindow | None]:
    """Decide whether this case passes, then place the fault window if not."""
    failing = rng.random() < packet_loss_rate
    if not failing:
        return "passed", None
    if packet_count < 8:
        return "failed", FaultWindow(start_seq=1, end_seq=max(1, packet_count - 2))
    width = max(4, packet_count // 12)
    start = rng.randint(1, max(1, packet_count - width - 1))
    return "failed", FaultWindow(start_seq=start, end_seq=start + width)


def generate_packets(
    *,
    run_id: int,
    test_case_id: int,
    attempt: int,
    packet_count: int,
    forced_outcome: str | None = None,
    packet_loss_rate: float = DEFAULT_PACKET_LOSS_RATE,
) -> tuple[str, FaultWindow | None, list[PacketSpec]]:
    rng = random.Random(derive_seed(run_id, test_case_id, attempt))
    if forced_outcome in {"passed", "failed"}:
        if forced_outcome == "passed":
            outcome: str = "passed"
            window: FaultWindow | None = None
        else:
            outcome = "failed"
            if packet_count < 8:
                window = FaultWindow(
                    start_seq=1, end_seq=max(1, packet_count - 2)
                )
            else:
                width = max(4, packet_count // 12)
                start = rng.randint(1, max(1, packet_count - width - 1))
                window = FaultWindow(start_seq=start, end_seq=start + width)
    else:
        outcome, window = choose_outcome(
            test_case_id, packet_count, packet_loss_rate, rng
        )

    stream_rng = random.Random(derive_seed(run_id, test_case_id, attempt) ^ 0x9E3779B9)
    packets: list[PacketSpec] = []
    for seq in range(1, packet_count + 1):
        payload = bytes(stream_rng.getrandbits(8) for _ in range(PACKET_BYTES))
        in_window = (
            window is not None and window.start_seq <= seq <= window.end_seq
        )
        rtt_ms = (
            round(stream_rng.uniform(180.0, 420.0), 2)
            if in_window
            else round(stream_rng.uniform(0.6, 9.5), 2)
        )
        packets.append(
            PacketSpec(
                seq=seq,
                payload=payload,
                ack=not in_window,
                rtt_ms=rtt_ms,
            )
        )
    return outcome, window, packets
