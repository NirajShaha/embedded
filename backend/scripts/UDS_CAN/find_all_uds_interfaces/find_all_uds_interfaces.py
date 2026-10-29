import can
import csv
import time
from ASC_Logger import ASCLogger


# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

SCAN_START = 0x400
SCAN_END = 0x500

REQUEST = [
    0x02,
    0x10,
    0x03,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00
]

OUTPUT_CSV = "diagnostic_ids.csv"

# ----------------------------------------------------
# Open Bus
# ----------------------------------------------------

bus = can.Bus(
    interface="vector",
    channel=0,
    app_name="Python",
    fd=True,
    receive_own_messages=True
)

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

