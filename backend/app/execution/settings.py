"""Tunable constants for the test-case execution engine.

The engine is designed for long-running ECU security scripts (4-5 hours per
script in production). The per-case duration and packet cadence are parameters
so the same code path serves both the current 1-2 minute demo runs and the
future multi-hour runs without changes.
"""

DEFAULT_CASE_DURATION_S = 30
MIN_CASE_DURATION_S = 15
MAX_CASE_DURATION_S = 8 * 3600

PACKET_INTERVAL_S = 0.25
PACKET_BYTES = 16
BUCKET_S = 1
BUCKET_FLUSH_EVERY_S = 5

# Packet persistence is sampled: every SAMPLE_EVERY-th packet plus every NACK
# plus the first/last two frames of each case. Buckets (per-second rollups)
# carry the full-fidelity trend data for charts; sampled packets back the live
# stream replay and the report inspector without storing millions of rows on
# 4-5h runs.
PACKET_SAMPLE_EVERY = 8

WS_HEARTBEAT_S = 15
WS_QUEUE_SIZE = 1000
PACKET_RING_BUFFER = 200

MAX_CASES_PER_RUN = 200
MAX_RUN_WALL_CLOCK_S = 12 * 3600

DEFAULT_PACKET_LOSS_RATE = 0.02
