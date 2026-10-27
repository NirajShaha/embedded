import can

import time

from ASC_Logger import ASCLogger

from bus_manager import bus


# ====================================================

# User Inputs

# ====================================================


def get_hex_input(prompt, default):
    value = input(

        f"{prompt} (default {default:X}): "

    ).strip()

    if value == "":
        return default

    return int(value, 16)


def get_float_input(prompt, default):
    value = input(

        f"{prompt} (default {default}): "

    ).strip()

    if value == "":
        return default

    return float(value)


print("\n=== Diagnostic Session Enumerator ===\n")

TX_ID = get_hex_input(

    "Enter TX ID",

    0x471

)

RX_ID = get_hex_input(

    "Enter RX ID",

    0x479

)

REQUEST_TIMEOUT = get_float_input(

    "Enter Request Timeout (sec)",

    0.20

)

SCAN_START = get_hex_input(

    "Enter Scan Start Session",

    0x7F

)

SCAN_END = get_hex_input(

    "Enter Scan End Session",

    0x00

)

# ====================================================

# Fixed Timing Parameters

# ====================================================


DEFAULT_SESSION_DELAY = 0.20

SESSION_ENTRY_DELAY = 0.20

# ====================================================

# Known Session Names

# ====================================================


SESSION_NAMES = {

    0x01: "Default Session",

    0x02: "Programming Session",

    0x03: "Extended Session",

    0x04: "Safety Session"

}

# ====================================================

# Display Configuration

# ====================================================


print("\nSelected Configuration")

print("--------------------------------")

print(f"TX ID           : 0x{TX_ID:X}")

print(f"RX ID           : 0x{RX_ID:X}")

print(f"Timeout         : {REQUEST_TIMEOUT}")

print(f"Scan Start      : 0x{SCAN_START:02X}")

print(f"Scan End        : 0x{SCAN_END:02X}")

print("--------------------------------\n")

# ====================================================

# Logger

# ====================================================


logger = ASCLogger()


# ====================================================

# Helper Functions

# ====================================================


def wait_for_response(session_id):
    end_time = (

            time.time()

            + REQUEST_TIMEOUT

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

        if msg.arbitration_id != RX_ID:
            continue

        # Positive Response

        if (

                len(msg.data) >= 3

                and msg.data[1] == 0x50

                and msg.data[2] == session_id

        ):
            return True

        # Negative Response

        if (

                len(msg.data) >= 4

                and msg.data[1] == 0x7F

                and msg.data[2] == 0x10

        ):
            return False

    return False


def send_session_request(session_id):
    msg = can.Message(

        arbitration_id=TX_ID,

        is_extended_id=False,

        data=[

            0x02,

            0x10,

            session_id,

            0x00,

            0x00,

            0x00,

            0x00,

            0x00

        ]

    )

    bus.send(msg)

    pass

    return wait_for_response(

        session_id

    )


# ====================================================

# Main

# ====================================================


supported_sessions = []

print(

    "\nStarting Diagnostic Session Enumeration...\n"

)

try:

    logger.start_log(

        "Diagnostic_Session_Enumeration",

        filters=[

            TX_ID,

            RX_ID

        ]

    )

    #

    # Ensure ECU starts from Default

    #

    send_session_request(

        0x01

    )

    time.sleep(1.0)

    for session in range(

            SCAN_START,

            SCAN_END - 1,

            -1):

        print(

            f"Checking Session 0x{session:02X}"

        )

        #

        # Return ECU to Default Session

        #

        send_session_request(

            0x01

        )

        time.sleep(

            DEFAULT_SESSION_DELAY

        )

        #

        # Test Session

        #

        positive = send_session_request(

            session

        )

        if positive:

            if session not in supported_sessions:
                supported_sessions.append(

                    session

                )

            print(

                f"[+] Supported Session "

                f"0x{session:02X}"

            )

            #

            # Allow ECU to settle

            #

            time.sleep(

                SESSION_ENTRY_DELAY

            )


except KeyboardInterrupt:

    print(

        "\nScan Stopped By User"

    )


finally:

    logger.stop_log()

    bus.shutdown()

# ====================================================

# Results

# ====================================================


supported_sessions.sort()

print("\n")

print(

    "Enumerated Diagnostic Sessions:"

)

print(

    "+------------+----------------------------+"

)

print(

    "| Session ID | Description                |"

)

print(

    "+------------+----------------------------+"

)

for session in supported_sessions:
    description = SESSION_NAMES.get(

        session,

        f"OEM Session 0x{session:02X}"

    )

    print(

        f"| 0x{session:02X}       | "

        f"{description:<26}|"

    )

print(

    "+------------+----------------------------+"

)

print(

    f"\nTotal Supported Sessions: "

    f"{len(supported_sessions)}"

)
