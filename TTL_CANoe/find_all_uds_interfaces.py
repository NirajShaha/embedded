import can
import csv
import time
from ASC_Logger import ASCLogger
import can_env


# ----------------------------------------------------
# Configuration
# ----------------------------------------------------
# Values come from the environment when launched by the backend (the Source ID
# and Destination ID from the dashboard map to the scan range, and the manual
# message maps to the request payload), and fall back to the original
# hard-coded defaults when the script is run by hand.

SCAN_START = can_env.scan_start(0x400)
SCAN_END = can_env.scan_end(0x500)

REQUEST = can_env.request_bytes("02 10 03 00 00 00 00 00")

OUTPUT_CSV = "diagnostic_ids.csv"

print(
    f"Scan range 0x{SCAN_START:03X} - 0x{SCAN_END:03X} | "
    f"request {' '.join(f'{b:02X}' for b in REQUEST)}",
    flush=True,
)

# ----------------------------------------------------
# Open Bus
# ----------------------------------------------------

bus = can.Bus(**can_env.bus_kwargs())

# ----------------------------------------------------
# Results Store
# ----------------------------------------------------

discovered_pairs = []

print(
    "\nStarting Diagnostic ID Enumeration...\n"
)

try:

    logger = ASCLogger()

    logger.start_log("Source_and_Destination_Id")

    for source_id in range(
        SCAN_START,
        SCAN_END + 1
    ):

        request = can.Message(
            arbitration_id=source_id,
            is_extended_id=False,
            data=REQUEST
        )

        bus.send(request)

        pass

        end_time = (
            time.time() + 0.05
        )

        while time.time() < end_time:

            msg = bus.recv(
                timeout=0.01
            )

            if msg is None:
                continue

            logger.log_frame(

                msg,

                "Rx"

            )

            if (
                len(msg.data) >= 3
                and (
                    msg.data[1] == 0x50 and msg.data[2] == 0x03
                )
            ):

                discovered_pairs.append(
                    (
                        source_id,
                        msg.arbitration_id
                    )
                )

                print(
                    f"[+] Found: "
                    f"0x{source_id:03X}"
                    f" -> "
                    f"0x{msg.arbitration_id:03X}"
                )

        if source_id % 100 == 0:

            print(
                f"Scanning 0x{source_id:03X}"
            )

except KeyboardInterrupt:

    print("\nScan Stopped")

finally:

    logger.stop_log()

    bus.shutdown()

# ----------------------------------------------------
# Save CSV
# ----------------------------------------------------

with open(
    OUTPUT_CSV,
    "w",
    newline=""
) as csv_file:

    writer = csv.writer(
        csv_file
    )

    writer.writerow(
        [
            "Source",
            "Destination"
        ]
    )

    for source, destination in discovered_pairs:
        writer.writerow(
            [
                f"0x{source:03X}",
                f"0x{destination:03X}"
            ]
        )

# ----------------------------------------------------
# Display Result
# ----------------------------------------------------

print("\n")

print(
    "Enumerated Diagnostic CAN ID:"
)

print(
    "+-----------------+-----------------+"
)

print(
    "|     Source      |   Destination   |"
)

print(
    "+-----------------+-----------------+"
)

for source, destination in discovered_pairs:

    print(
        f"| 0x{source:03X}         "
        f"| 0x{destination:03X}         |"
    )

print(
    "+-----------------+-----------------+"
)

print(
    f"\nResults saved to {OUTPUT_CSV}"
)

