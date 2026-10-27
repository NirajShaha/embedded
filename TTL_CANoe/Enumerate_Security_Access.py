import time
import can

from ASC_Logger import ASCLogger


# ====================================================
# Vector CAN Configuration
# ====================================================

CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"

CAN_FD_ENABLED = True
CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000

USE_EXTENDED_CAN_ID = False


# ====================================================
# Security Access Enumeration Configuration
# ====================================================
#
# UDS SecurityAccess:
#
# Odd subfunctions:
#     Request Seed
#
# Even subfunctions:
#     Send Key
#
# The configured range is 0x00 to 0x7F, but this
# scanner sends only odd request-seed subfunctions:
#
#     0x01, 0x03, 0x05 ... 0x7F
#
# No key values are generated or transmitted.
# ====================================================

SECURITY_SCAN_START = 0x00
SECURITY_SCAN_END = 0x7F

DEFAULT_RESPONSE_TIMEOUT = 0.50
DEFAULT_REQUEST_INTERVAL = 0.10

DEFAULT_SESSION_DELAY = 0.50
SESSION_ENTRY_DELAY = 0.50


# ====================================================
# Diagnostic Sessions
# ====================================================

SESSION_NAMES = {
    0x01: "Default Session",
    0x02: "Programming Session",
    0x03: "Extended Session",
    0x04: "Safety System Session"
}


# Sessions scanned when ALL is selected.
#
# Add confirmed OEM sessions if required.

ALL_SESSIONS = [
    0x01,
    0x02,
    0x03
]


# ====================================================
# NRC Names
# ====================================================

NRC_NAMES = {
    0x10: "General Reject",
    0x11: "Service Not Supported",
    0x12: "Sub-function Not Supported",
    0x13: "Incorrect Message Length Or Invalid Format",
    0x14: "Response Too Long",
    0x21: "Busy Repeat Request",
    0x22: "Conditions Not Correct",
    0x24: "Request Sequence Error",
    0x25: "No Response From Subnet Component",
    0x26: "Failure Prevents Execution",
    0x31: "Request Out Of Range",
    0x33: "Security Access Denied",
    0x35: "Invalid Key",
    0x36: "Exceeded Number Of Attempts",
    0x37: "Required Time Delay Not Expired",
    0x70: "Upload Or Download Not Accepted",
    0x71: "Transfer Data Suspended",
    0x72: "General Programming Failure",
    0x73: "Wrong Block Sequence Counter",
    0x78: "Response Pending",
    0x7E: "Sub-function Not Supported In Active Session",
    0x7F: "Service Not Supported In Active Session"
}


# ====================================================
# Security Access NRC Classification
# ====================================================
#
# A positive 67 <odd-subfunction> response confirms
# that the request-seed subfunction is supported.
#
# These NRCs indicate that SID 0x27 or the security
# request was recognised, but the request could not
# be completed because of ECU conditions, sequencing,
# security restrictions, or a required delay.
# ====================================================

RECOGNISED_SECURITY_NRCS = {
    0x10,
    0x13,
    0x21,
    0x22,
    0x24,
    0x25,
    0x26,
    0x33,
    0x36,
    0x37
}


# These NRCs are excluded from the supported list for
# the selected diagnostic session.

NOT_SUPPORTED_SECURITY_NRCS = {
    0x11,
    0x12,
    0x31,
    0x7E,
    0x7F
}


# ====================================================
# Runtime Objects
# ====================================================

bus = None

TX_ID = None
RX_ID = None

RESPONSE_TIMEOUT = None
REQUEST_INTERVAL = None


# ====================================================
# User Input Functions
# ====================================================

def get_hex_input(prompt, default):

    while True:

        value = input(
            f"{prompt} (default 0x{default:X}): "
        ).strip()

        if value == "":
            return default

        try:

            converted_value = int(
                value,
                16
            )

            if converted_value < 0:
                raise ValueError

            return converted_value

        except ValueError:

            print("[!] Invalid hexadecimal value.")
            print("    Examples: 471, 0x471, 7E0")


def get_float_input(prompt, default):

    while True:

        value = input(
            f"{prompt} (default {default} seconds): "
        ).strip()

        if value == "":
            return default

        try:

            converted_value = float(
                value
            )

            if converted_value <= 0:
                raise ValueError

            return converted_value

        except ValueError:

            print(
                "[!] Enter a numeric value greater "
                "than zero."
            )


def get_session_selection():

    print()
    print("==================================================")
    print("Diagnostic Session Selection")
    print("==================================================")
    print("Enter one diagnostic session ID:")
    print()
    print("  01    Default Session")
    print("  02    Programming Session")
    print("  03    Extended Session")
    print("  04    Safety System Session")
    print()
    print("Other options:")
    print()
    print("  ALL   Scan all configured sessions")
    print("  NONE  Use the ECU's current active session")
    print()
    print("Examples:")
    print()
    print("  Select session: 01")
    print("  Select session: 02")
    print("  Select session: 03")
    print("  Select session: ALL")
    print("  Select session: NONE")
    print("==================================================")

    while True:

        value = input(
            "Select session: "
        ).strip()

        if value.upper() == "ALL":

            return {
                "mode": "ALL",
                "sessions": ALL_SESSIONS.copy()
            }

        if value.upper() == "NONE":

            return {
                "mode": "NONE",
                "sessions": [None]
            }

        try:

            session_id = int(
                value,
                16
            )

            if not 0x00 <= session_id <= 0x7F:

                print(
                    "[!] Session ID must be between "
                    "0x00 and 0x7F."
                )

                continue

            return {
                "mode": "SINGLE",
                "sessions": [session_id]
            }

        except ValueError:

            print(
                "[!] Enter one hexadecimal session ID, "
                "ALL, or NONE."
            )


# ====================================================
# CAN Bus Creation
# ====================================================

def create_can_bus():

    print()
    print("[*] Opening Vector CAN interface...")

    created_bus = can.Bus(
        interface=CAN_INTERFACE,
        channel=CAN_CHANNEL,
        app_name=CAN_APP_NAME,
        fd=CAN_FD_ENABLED,
        bitrate=CAN_BITRATE,
        dbitrate=CAN_DATA_BITRATE,
        receive_own_messages=True
    )

    print("[+] Vector CAN interface opened.")

    return created_bus


# ====================================================
# ISO-TP Single-Frame Helpers
# ====================================================

def create_single_frame(payload):

    if not payload:

        raise ValueError(
            "UDS payload cannot be empty."
        )

    if len(payload) > 7:

        raise ValueError(
            "Classic ISO-TP single-frame payload "
            "cannot exceed seven UDS bytes."
        )

    frame_data = [
        len(payload)
    ]

    frame_data.extend(
        payload
    )

    while len(frame_data) < 8:

        frame_data.append(
            0x00
        )

    return frame_data


def extract_single_frame_payload(message):

    if len(message.data) < 2:
        return None

    pci_type = (
        message.data[0] >> 4
    )

    if pci_type != 0x00:
        return None

    payload_length = (
        message.data[0] & 0x0F
    )

    if payload_length == 0:
        return None

    if payload_length > len(message.data) - 1:
        return None

    return bytes(
        message.data[
            1:1 + payload_length
        ]
    )


# ====================================================
# CAN Communication Helpers
# ====================================================

def drain_receive_buffer():

    if bus is None:
        return

    while True:

        message = bus.recv(
            timeout=0.001
        )

        if message is None:
            break


def send_uds_request(
        payload,
        logger):

    message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=USE_EXTENDED_CAN_ID,
        is_fd=False,
        data=create_single_frame(
            payload
        )
    )

    bus.send(
        message
    )

    # ASCLogger uses the timestamp to calculate the
    # relative time. A locally created Tx message may
    # not have a timestamp assigned by python-can.

    if not getattr(
            message,
            "timestamp",
            None
    ):

        message.timestamp = time.time()

    pass


# ====================================================
# Diagnostic Session Response Handler
# ====================================================

def wait_for_session_response(
        requested_session,
        logger):

    deadline = (
        time.monotonic()
        + RESPONSE_TIMEOUT
    )

    response_pending_received = False

    while time.monotonic() < deadline:

        remaining_time = (
            deadline
            - time.monotonic()
        )

        receive_timeout = min(
            0.01,
            max(
                remaining_time,
                0.0
            )
        )

        message = bus.recv(
            timeout=receive_timeout
        )

        if message is None:
            continue

        logger.log_frame(
            message,
            "Rx"
        )

        if message.arbitration_id != RX_ID:
            continue

        payload = extract_single_frame_payload(
            message
        )

        if payload is None:
            continue

        # Positive Diagnostic Session Control:
        #
        # 50 <session> [timing parameters]

        if (
            len(payload) >= 2
            and payload[0] == 0x50
            and (
                payload[1] & 0x7F
            ) == (
                requested_session & 0x7F
            )
        ):

            return {
                "entered": True,
                "nrc": None,
                "payload": payload,
                "response_pending": (
                    response_pending_received
                )
            }

        # Negative Diagnostic Session Control:
        #
        # 7F 10 <NRC>

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1] == 0x10
        ):

            nrc = payload[2]

            if nrc == 0x78:

                response_pending_received = True

                # NRC 0x78 is intermediate.
                # Restart the timeout and wait for the
                # final positive or negative response.

                deadline = (
                    time.monotonic()
                    + RESPONSE_TIMEOUT
                )

                continue

            return {
                "entered": False,
                "nrc": nrc,
                "payload": payload,
                "response_pending": (
                    response_pending_received
                )
            }

    return {
        "entered": False,
        "nrc": None,
        "payload": None,
        "response_pending": response_pending_received
    }


# ====================================================
# Diagnostic Session Control
# ====================================================

def enter_diagnostic_session(
        session_id,
        logger):

    drain_receive_buffer()

    send_uds_request(
        [
            0x10,
            session_id
        ],
        logger
    )

    result = wait_for_session_response(
        session_id,
        logger
    )

    if result["entered"]:

        time.sleep(
            SESSION_ENTRY_DELAY
        )

    return result


def prepare_testing_session(
        session_id,
        logger,
        show_output=True):

    if session_id is None:

        return {
            "entered": True,
            "nrc": None,
            "payload": None,
            "response_pending": False
        }

    # For non-default sessions, request the Default
    # Session before requesting the selected session.

    if session_id != 0x01:

        if show_output:

            print(
                "[*] Requesting Default Session..."
            )

        default_result = enter_diagnostic_session(
            0x01,
            logger
        )

        if not default_result["entered"]:

            if show_output:

                if default_result["nrc"] is not None:

                    nrc_name = NRC_NAMES.get(
                        default_result["nrc"],
                        "Unknown NRC"
                    )

                    print(
                        f"[!] Default Session returned "
                        f"NRC 0x{default_result['nrc']:02X}: "
                        f"{nrc_name}"
                    )

                else:

                    print(
                        "[!] No conclusive response for "
                        "Default Session."
                    )

            return default_result

        if show_output:

            print(
                "[+] Default Session entered."
            )

        time.sleep(
            DEFAULT_SESSION_DELAY
        )

    if show_output:

        print(
            f"[*] Requesting testing Session "
            f"0x{session_id:02X}..."
        )

    selected_result = enter_diagnostic_session(
        session_id,
        logger
    )

    if show_output:

        if selected_result["entered"]:

            print(
                f"[+] Testing Session "
                f"0x{session_id:02X} entered."
            )

        elif selected_result["nrc"] is not None:

            nrc_name = NRC_NAMES.get(
                selected_result["nrc"],
                "Unknown NRC"
            )

            print(
                f"[!] Testing Session "
                f"0x{session_id:02X} returned NRC "
                f"0x{selected_result['nrc']:02X}: "
                f"{nrc_name}"
            )

        else:

            print(
                f"[!] No conclusive response while "
                f"entering Session "
                f"0x{session_id:02X}."
            )

    return selected_result


# ====================================================
# Security Access Response Handler
# ====================================================

def wait_for_security_response(
        requested_subfunction,
        logger):

    deadline = (
        time.monotonic()
        + RESPONSE_TIMEOUT
    )

    response_pending_received = False

    while time.monotonic() < deadline:

        remaining_time = (
            deadline
            - time.monotonic()
        )

        receive_timeout = min(
            0.01,
            max(
                remaining_time,
                0.0
            )
        )

        message = bus.recv(
            timeout=receive_timeout
        )

        if message is None:
            continue

        logger.log_frame(
            message,
            "Rx"
        )

        if message.arbitration_id != RX_ID:
            continue

        payload = extract_single_frame_payload(
            message
        )

        if payload is None:
            continue

        # Positive SecurityAccess response:
        #
        # 67 <request-seed subfunction> <seed bytes>
        #
        # The seed bytes are captured only in the ASC
        # log. They are not processed by this script.

        if (
            len(payload) >= 2
            and payload[0] == 0x67
            and (
                payload[1] & 0x7F
            ) == (
                requested_subfunction & 0x7F
            )
        ):

            seed_length = max(
                len(payload) - 2,
                0
            )

            seed_is_zero = False

            if seed_length > 0:

                seed_data = payload[2:]

                seed_is_zero = all(
                    byte == 0x00
                    for byte in seed_data
                )

            return {
                "supported": True,
                "classification": "Positive Response",
                "nrc": None,
                "payload": payload,
                "seed_length": seed_length,
                "seed_is_zero": seed_is_zero,
                "response_pending": (
                    response_pending_received
                )
            }

        # Negative SecurityAccess response:
        #
        # 7F 27 <NRC>

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1] == 0x27
        ):

            nrc = payload[2]

            # NRC 0x78 is intermediate.
            #
            # Do not send the next request. Restart the
            # configured response timeout and continue
            # waiting for a final response.

            if nrc == 0x78:

                response_pending_received = True

                print(
                    "    [*] NRC 0x78 received. "
                    "Waiting for final response..."
                )

                deadline = (
                    time.monotonic()
                    + RESPONSE_TIMEOUT
                )

                continue

            if nrc in RECOGNISED_SECURITY_NRCS:

                return {
                    "supported": True,
                    "classification":
                        "Recognised By NRC",
                    "nrc": nrc,
                    "payload": payload,
                    "seed_length": 0,
                    "seed_is_zero": False,
                    "response_pending": (
                        response_pending_received
                    )
                }

            if nrc in NOT_SUPPORTED_SECURITY_NRCS:

                return {
                    "supported": False,
                    "classification":
                        "Not Supported",
                    "nrc": nrc,
                    "payload": payload,
                    "seed_length": 0,
                    "seed_is_zero": False,
                    "response_pending": (
                        response_pending_received
                    )
                }

            return {
                "supported": False,
                "classification":
                    "Unclassified NRC",
                "nrc": nrc,
                "payload": payload,
                "seed_length": 0,
                "seed_is_zero": False,
                "response_pending": (
                    response_pending_received
                )
            }

    if response_pending_received:

        classification = (
            "Timeout After Response Pending"
        )

    else:

        classification = (
            "No Response"
        )

    return {
        "supported": False,
        "classification": classification,
        "nrc": None,
        "payload": None,
        "seed_length": 0,
        "seed_is_zero": False,
        "response_pending": response_pending_received
    }


# ====================================================
# Test One Request-Seed Subfunction
# ====================================================

def test_seed_subfunction(
        subfunction,
        logger):

    drain_receive_buffer()

    print(
        f"Checking Security Seed Subfunction "
        f"0x{subfunction:02X}",
        end=""
    )

    send_uds_request(
        [
            0x27,
            subfunction
        ],
        logger
    )

    return wait_for_security_response(
        subfunction,
        logger
    )


# ====================================================
# Generate Odd Request-Seed Subfunctions
# ====================================================

def get_seed_subfunctions():

    seed_subfunctions = []

    for subfunction in range(
            SECURITY_SCAN_START,
            SECURITY_SCAN_END + 1
    ):

        # Odd subfunctions are Request Seed.
        # Even subfunctions are Send Key.

        if subfunction % 2 == 1:

            seed_subfunctions.append(
                subfunction
            )

    return seed_subfunctions


# ====================================================
# Security Access Scanner
# ====================================================

def scan_security_levels(
        session_id,
        logger):

    supported_levels = []

    seed_subfunctions = get_seed_subfunctions()

    print()
    print(
        f"Configured subfunction range: "
        f"0x{SECURITY_SCAN_START:02X} to "
        f"0x{SECURITY_SCAN_END:02X}"
    )

    print(
        "Testing only odd request-seed subfunctions:"
    )

    print(
        "0x01, 0x03, 0x05 ... 0x7F"
    )

    print()

    for index, subfunction in enumerate(
            seed_subfunctions
    ):

        result = test_seed_subfunction(
            subfunction,
            logger
        )

        if result["supported"]:

            supported_levels.append({
                "subfunction": subfunction,
                "classification":
                    result["classification"],
                "nrc": result["nrc"],
                "seed_length":
                    result["seed_length"],
                "seed_is_zero":
                    result["seed_is_zero"]
            })

            if result["nrc"] is None:

                print(
                    "  [+] Positive seed response"
                )

                print(
                    f"    [*] Seed length: "
                    f"{result['seed_length']} byte(s)"
                )

                if result["seed_is_zero"]:

                    print(
                        "    [*] ECU returned an "
                        "all-zero seed."
                    )

            else:

                nrc_name = NRC_NAMES.get(
                    result["nrc"],
                    "Unknown NRC"
                )

                print(
                    f"  [+] Security level recognised, "
                    f"NRC 0x{result['nrc']:02X} "
                    f"({nrc_name})"
                )

        else:

            if result["nrc"] is not None:

                nrc_name = NRC_NAMES.get(
                    result["nrc"],
                    "Unknown NRC"
                )

                print(
                    f"  [-] NRC "
                    f"0x{result['nrc']:02X} "
                    f"({nrc_name})"
                )

            else:

                print(
                    f"  [-] "
                    f"{result['classification']}"
                )

        # The interval is applied only after response
        # handling for the current request is complete.

        if index < len(seed_subfunctions) - 1:

            time.sleep(
                REQUEST_INTERVAL
            )

    return supported_levels


# ====================================================
# Security-Level Description
# ====================================================

def get_security_level_description(
        seed_subfunction):

    # Request-seed subfunctions are odd:
    #
    # 0x01 -> Security Level 1
    # 0x03 -> Security Level 2
    # 0x05 -> Security Level 3

    level_number = (
        seed_subfunction + 1
    ) // 2

    return (
        f"Request Seed Level {level_number}"
    )


# ====================================================
# Result Display
# ====================================================

def display_security_results(
        session_id,
        security_levels):

    if session_id is None:

        session_text = (
            "Current Active Session"
        )

    else:

        session_name = SESSION_NAMES.get(
            session_id,
            f"OEM Session 0x{session_id:02X}"
        )

        session_text = (
            f"Session 0x{session_id:02X} "
            f"({session_name})"
        )

    print()
    print()
    print(
        f"Enumerated Security Levels for "
        f"{session_text}:"
    )

    print()

    print(
        "+------------+--------------------------------------+"
    )

    print(
        "| Level      | Description                          |"
    )

    print(
        "+------------+--------------------------------------+"
    )

    for result in security_levels:

        subfunction = result[
            "subfunction"
        ]

        description = get_security_level_description(
            subfunction
        )

        print(
            f"| 0x{subfunction:02X}       | "
            f"{description:<36} |"
        )

    print(
        "+------------+--------------------------------------+"
    )

    print(
        f"\nTotal recognised security seed levels: "
        f"{len(security_levels)}"
    )


# ====================================================
# ASC Log Name
# ====================================================

def get_log_name(
        session_id):

    if session_id is None:

        return (
            "Security_Access_Enumeration_"
            "Current_Active_Session"
        )

    session_name = SESSION_NAMES.get(
        session_id,
        "OEM_Session"
    )

    safe_session_name = (
        session_name.replace(
            " ",
            "_"
        )
    )

    return (
        f"Security_Access_Enumeration_"
        f"Session_{session_id:02X}_"
        f"{safe_session_name}"
    )


# ====================================================
# Scan One Diagnostic Session
# ====================================================

def scan_selected_session(
        session_id):

    logger = ASCLogger()

    log_name = get_log_name(
        session_id
    )

    security_levels = []
    session_ready = False
    log_started = False

    print()
    print("=" * 64)

    if session_id is None:

        print(
            "Selected Session: NONE"
        )

        print(
            "The ECU's current active session "
            "will be used."
        )

    else:

        session_name = SESSION_NAMES.get(
            session_id,
            f"OEM Session 0x{session_id:02X}"
        )

        print(
            f"Selected Session: "
            f"0x{session_id:02X} "
            f"({session_name})"
        )

    print(
        f"ASC Log Name: {log_name}"
    )

    print("=" * 64)

    try:

        logger.start_log(
            log_name,
            filters=[
                TX_ID,
                RX_ID
            ]
        )

        log_started = True

        if session_id is None:

            session_ready = True

            print(
                "[*] No Diagnostic Session Control "
                "request will be sent."
            )

        else:

            print(
                f"[*] Preparing testing Session "
                f"0x{session_id:02X}..."
            )

            session_result = prepare_testing_session(
                session_id,
                logger,
                show_output=True
            )

            if session_result["entered"]:

                session_ready = True

            elif session_result["nrc"] is not None:

                nrc_name = NRC_NAMES.get(
                    session_result["nrc"],
                    "Unknown NRC"
                )

                print(
                    f"[!] Unable to enter Session "
                    f"0x{session_id:02X}."
                )

                print(
                    f"[!] NRC "
                    f"0x{session_result['nrc']:02X}: "
                    f"{nrc_name}"
                )

            else:

                print(
                    f"[!] Session 0x{session_id:02X} "
                    "was not confirmed."
                )

        if session_ready:

            security_levels = scan_security_levels(
                session_id,
                logger
            )

            display_security_results(
                session_id,
                security_levels
            )

        else:

            print(
                "[!] Security Access enumeration "
                "skipped because the selected session "
                "could not be entered."
            )

    except KeyboardInterrupt:

        print()
        print(
            "[!] Session scan interrupted by user."
        )

        raise

    finally:

        # Return the ECU to Default Session after an
        # explicitly selected session.
        #
        # NONE mode does not modify the ECU session.

        if (
            session_id is not None
            and session_ready
            and bus is not None
        ):

            try:

                print()
                print(
                    "[*] Returning ECU to "
                    "Default Session..."
                )

                default_result = (
                    enter_diagnostic_session(
                        0x01,
                        logger
                    )
                )

                if default_result["entered"]:

                    print(
                        "[+] ECU returned to "
                        "Default Session."
                    )

                elif default_result["nrc"] is not None:

                    nrc_name = NRC_NAMES.get(
                        default_result["nrc"],
                        "Unknown NRC"
                    )

                    print(
                        f"[!] Default Session returned "
                        f"NRC "
                        f"0x{default_result['nrc']:02X}: "
                        f"{nrc_name}"
                    )

                else:

                    print(
                        "[!] Default Session return "
                        "was not confirmed."
                    )

            except KeyboardInterrupt:

                print(
                    "[!] Default Session cleanup "
                    "interrupted."
                )

            except can.CanError as error:

                print(
                    f"[!] CAN error during Default "
                    f"Session cleanup: {error}"
                )

            except Exception as error:

                print(
                    f"[!] Default Session cleanup "
                    f"error: {error}"
                )

        if log_started:

            try:

                logger.stop_log()

                print(
                    f"[+] ASC log closed: {log_name}"
                )

            except Exception as error:

                print(
                    f"[!] ASC log close error: {error}"
                )

    return security_levels


# ====================================================
# Programme Start
# ====================================================

print()
print("==================================================")
print("     Security Access Level Enumeration Tool")
print("==================================================")
print()

TX_ID = get_hex_input(
    "Enter TX CAN ID",
    0x471
)

RX_ID = get_hex_input(
    "Enter RX CAN ID",
    0x479
)

RESPONSE_TIMEOUT = get_float_input(
    "Enter maximum response timeout for each request",
    DEFAULT_RESPONSE_TIMEOUT
)

REQUEST_INTERVAL = get_float_input(
    "Enter time between consecutive requests",
    DEFAULT_REQUEST_INTERVAL
)

SESSION_SELECTION = get_session_selection()

SELECTED_SESSIONS = SESSION_SELECTION[
    "sessions"
]


# ====================================================
# Display Selected Configuration
# ====================================================

print()
print("Selected Configuration")
print("--------------------------------------------------")
print(f"TX CAN ID          : 0x{TX_ID:X}")
print(f"RX CAN ID          : 0x{RX_ID:X}")

print(
    f"Response timeout   : "
    f"{RESPONSE_TIMEOUT} seconds"
)

print(
    f"Request interval   : "
    f"{REQUEST_INTERVAL} seconds"
)

print(
    f"Configured range   : "
    f"0x{SECURITY_SCAN_START:02X} to "
    f"0x{SECURITY_SCAN_END:02X}"
)

print(
    "Actual requests    : Odd subfunctions only"
)

print(
    "Seed requests      : "
    "0x01, 0x03, 0x05 ... 0x7F"
)

if SESSION_SELECTION["mode"] == "ALL":

    print(
        "Session selection   : ALL"
    )

    print(
        "Sessions            : "
        + ", ".join(
            f"0x{session:02X}"
            for session in SELECTED_SESSIONS
        )
    )

elif SESSION_SELECTION["mode"] == "NONE":

    print(
        "Session selection   : NONE"
    )

    print(
        "Action              : Use current active session"
    )

else:

    selected_session = (
        SELECTED_SESSIONS[0]
    )

    print(
        f"Session selection   : "
        f"0x{selected_session:02X}"
    )

print("--------------------------------------------------")


# ====================================================
# Execute Security Access Enumeration
# ====================================================

all_results = {}

try:

    bus = create_can_bus()

    print()
    print(
        "[*] Starting Security Access "
        "seed-level enumeration..."
    )

    for selected_session in SELECTED_SESSIONS:

        session_results = scan_selected_session(
            selected_session
        )

        result_key = (
            "CURRENT"
            if selected_session is None
            else f"0x{selected_session:02X}"
        )

        all_results[
            result_key
        ] = {
            "session_id": selected_session,
            "security_levels": session_results
        }

except KeyboardInterrupt:

    print()
    print(
        "[!] Security Access enumeration "
        "stopped by user."
    )

except can.CanError as error:

    print()
    print(
        f"[!] CAN communication error: {error}"
    )

except Exception as error:

    print()
    print(
        f"[!] Unexpected error: {error}"
    )

finally:

    # Shut down the CAN bus exactly once.
    #
    # The bus is not shut down inside the session loop
    # or security-subfunction loop.

    if bus is not None:

        try:

            print()
            print(
                "[*] Shutting down Vector CAN interface..."
            )

            bus.shutdown()

            print(
                "[+] Vector CAN interface shut down."
            )

        except Exception as error:

            print(
                f"[!] CAN interface shutdown error: "
                f"{error}"
            )

        finally:

            bus = None


# ====================================================
# Final Result Summary
# ====================================================

print()
print("=" * 64)
print("Security Access Level Enumeration Completed")
print("=" * 64)

if not all_results:

    print(
        "No session scan was completed."
    )

else:

    for result_data in all_results.values():

        display_security_results(
            result_data["session_id"],
            result_data["security_levels"]
        )