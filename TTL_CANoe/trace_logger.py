from datetime import datetime

from bus_manager import bus
from can_tp import CanTp


print(
    "date",
    datetime.now().strftime(
        "%a %b %d %I:%M:%S.%f %p %Y"
    )[:-3]
)

print("base hex timestamps absolute")
print()

tp = CanTp(bus)


def print_trace(msg, direction):

    frame_type = "fd" if msg.is_fd else "d"

    data_text = " ".join(
        f"{b:02X}"
        for b in msg.data
    )

    print(
        f"{msg.timestamp:10.6f} "
        f"1 "
        f"{msg.arbitration_id:03X} "
        f"{direction:2} "
        f"{frame_type} "
        f"{len(msg.data)} "
        f"{data_text}"
    )


print("Trace Window Started")
print("Press CTRL+C to stop\n")

try:

    while True:

        msg = bus.recv()

        if msg is None:
            continue

        direction = "Rx"

        if msg.arbitration_id == 0x471:
            direction = "Tx"

        print_trace(
            msg,
            direction
        )

        fc_msg = tp.process(msg)

        if fc_msg:

            print_trace(
                fc_msg,
                "Tx"
            )

except KeyboardInterrupt:

    print("\nStopped")

finally:

    bus.shutdown()