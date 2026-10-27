import time
import can

from ASC_Logger import ASCLogger


# ====================================================
# Vector CAN Interface Configuration
# ====================================================

CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"

CAN_FD_ENABLED = True
CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000

USE_EXTENDED_CAN_ID = False


# ====================================================
# ECU Reset Enumeration Configuration
# ====================================================

RESET_SCAN_START = 0x00
RESET_SCAN_END = 0x7F

DEFAULT_RESPONSE_POLL_TIMEOUT = 0.50
DEFAULT_REQUEST_INTERVAL = 0.10
DEFAULT_ECU_RECOVERY_DELAY = 2.00

DEFAULT_SESSION_DELAY = 0.50
SESSION_ENTRY_DELAY = 0.50


# ====================================================
# Diagnostic Session Definitions
# ====================================================

SESSION_NAMES = {
    0x01: "Default Session",
    0x02: "Programming Session",
    0x03: "Extended Session",
    0x04: "Safety System Session"
}


# These sessions are tested when the user selects ALL.
# Add OEM-specific sessions if required.
#
# Example:
#
# ALL_SESSIONS = [
#     0x01,
#     0x02,
#     0x03,
#     0x04,
#     0x40,
#     0x60
# ]

ALL_SESSIONS = [
    0x01,
    0x02,
    0x03
]


# ====================================================
# ECU Reset Type Definitions
# ====================================================

ECU_RESET_TYPE_NAMES = {
    0x01: "Hard Reset",
    0x02: "Key Off-On Reset",
    0x03: "Soft Reset",
    0x04: "Enable Rapid Power Shutdown",
    0x05: "Disable Rapid Power Shutdown"
}


# ====================================================
# UDS Negative Response Code Definitions
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
# Reset-Type NRC Classification
# ====================================================
#
# The following NRCs indicate that the ECU recognised
# the ECU Reset request or reset type, but execution
# was rejected because of ECU conditions, security,
# request sequence, or another operating restriction.
# ====================================================

RECOGNISED_RESET_NRCS = {
    0x10,
    0x13,
    0x14,
    0x21,
    0x22,
    0x24,
    0x25,
    0x26,
    0x33,
    0x35,
    0x36,
    0x37,
    0x70,
    0x71,
    0x72,
    0x73
}


# The following NRCs mean that the ECU Reset service
# or reset type is not considered supported in the
# selected diagnostic session.

NOT_SUPPORTED_RESET_NRCS = {
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

RESPONSE_POLL_TIMEOUT = None
REQUEST_INTERVAL = None
ECU_RECOVERY_DELAY = None


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

            converted_value = int(value, 16)

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

            converted_value = float(value)

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

            session_id = int(value, 16)

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
# Vector CAN Bus Creation
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
# ISO-TP Single-Frame Functions
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

    frame_data = [len(payload)]

    frame_data.extend(payload)

    while len(frame_data) < 8:

        frame_data.append(0x00)

    return frame_data


def extract_single_frame_payload(message):

    if len(message.data) < 2:
        return None

    pci_type = message.data[0] >> 4

    if pci_type != 0x00:
        return None

    payload_length = message.data[0] & 0x0F

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
# General CAN Communication Functions
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


def send_uds_request(payload, logger):

    message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=USE_EXTENDED_CAN_ID,
        is_fd=False,
        data=create_single_frame(payload)
    )

    bus.send(message)

    # Locally created Tx messages might not receive
    # a timestamp from python-can. ASCLogger requires
    # the timestamp to calculate relative timing.

    if not getattr(
            message,
            "timestamp",
            None
    ):

        message.timestamp = time.time()

    pass


# ====================================================
# Session-Control Response Handler
# ====================================================

def wait_for_session_response(
        requested_session,
        logger):

    response_pending_received = False

    while True:

        message = bus.recv(
            timeout=RESPONSE_POLL_TIMEOUT
        )

        if message is None:

            if response_pending_received:

                print(
                    "    [*] Waiting for final session "
                    "response after NRC 0x78..."
                )

            else:

                print(
                    "    [*] No session response yet. "
                    "Continuing to wait..."
                )

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

        # Positive Diagnostic Session Control response:
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
                "final_response": True,
                "entered": True,
                "nrc": None,
                "payload": payload
            }

        # Negative Diagnostic Session Control response:
        #
        # 7F 10 <NRC>

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1] == 0x10
        ):

            nrc = payload[2]

            # NRC 0x78 is not a final response.
            # Continue waiting.

            if nrc == 0x78:

                response_pending_received = True

                print(
                    "    [*] Session Control NRC 0x78 "
                    "received."
                )

                print(
                    "    [*] Waiting for final positive "
                    "or negative response..."
                )

                continue

            return {
                "final_response": True,
                "entered": False,
                "nrc": nrc,
                "payload": payload
            }


# ====================================================
# Diagnostic Session Control Functions
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
            "final_response": True,
            "entered": True,
            "nrc": None,
            "payload": None
        }

    # For a non-default testing session, enter the
    # Default Session first.

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

    return selected_result


# ====================================================
# ECU Reset Response Handler
# ====================================================

def wait_for_ecu_reset_response(
        requested_reset_type,
        logger):

    response_pending_received = False

    print(
        "    [*] Waiting for final ECU Reset response..."
    )

    while True:

        # RESPONSE_POLL_TIMEOUT is only the bus receive
        # polling interval.
        #
        # If this call returns None, the scanner does
        # not send the next ECU Reset request.
        #
        # The scanner continues waiting until either:
        #
        # 1. Positive response 51 xx is received, or
        # 2. Final negative response 7F 11 yy is received.

        message = bus.recv(
            timeout=RESPONSE_POLL_TIMEOUT
        )

        if message is None:

            if response_pending_received:

                print(
                    "    [*] No final response received "
                    "after NRC 0x78."
                )

                print(
                    "    [*] Continuing to wait..."
                )

            else:

                print(
                    "    [*] No ECU Reset response yet."
                )

                print(
                    "    [*] Continuing to wait..."
                )

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

        # Positive ECU Reset response:
        #
        # 51 <reset type>

        if (
            len(payload) >= 2
            and payload[0] == 0x51
            and (
                payload[1] & 0x7F
            ) == (
                requested_reset_type & 0x7F
            )
        ):

            return {
                "final_response": True,
                "supported": True,
                "classification": "Positive Response",
                "nrc": None,
                "positive_reset": True,
                "payload": payload
            }

        # Negative ECU Reset response:
        #
        # 7F 11 <NRC>

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1] == 0x11
        ):

            nrc = payload[2]

            # NRC 0x78 means Response Pending.
            #
            # It is not considered the final response.
            #
            # Do not send the next request.
            # Do not restore the testing session.
            # Continue waiting.

            if nrc == 0x78:

                response_pending_received = True

                print(
                    "    [*] NRC 0x78 received: "
                    "Response Pending"
                )

                print(
                    "    [*] Waiting for final positive "
                    "or negative ECU Reset response..."
                )

                continue

            # Any NRC other than 0x78 is considered a
            # final negative response.
            #
            # The testing session is not restored after
            # a final NRC.

            if nrc in RECOGNISED_RESET_NRCS:

                return {
                    "final_response": True,
                    "supported": True,
                    "classification":
                        "Recognised By NRC",
                    "nrc": nrc,
                    "positive_reset": False,
                    "payload": payload
                }

            if nrc in NOT_SUPPORTED_RESET_NRCS:

                return {
                    "final_response": True,
                    "supported": False,
                    "classification":
                        "Not Supported",
                    "nrc": nrc,
                    "positive_reset": False,
                    "payload": payload
                }

            return {
                "final_response": True,
                "supported": False,
                "classification":
                    "Unclassified NRC",
                "nrc": nrc,
                "positive_reset": False,
                "payload": payload
            }


# ====================================================
# Test One ECU Reset Type
# ====================================================

def test_reset_type(
        reset_type,
        logger):

    drain_receive_buffer()

    print()
    print(
        f"Checking Reset Type 0x{reset_type:02X}"
    )

    send_uds_request(
        [
            0x11,
            reset_type
        ],
        logger
    )

    # This function returns only after receiving a
    # final positive or final negative response.
    #
    # NRC 0x78 does not complete the current request.

    return wait_for_ecu_reset_response(
        reset_type,
        logger
    )


# ====================================================
# Restore Testing Session After Positive Reset
# ====================================================

def restore_session_after_positive_reset(
        session_id,
        logger):

    print()
    print(
        "[*] Positive ECU Reset response received."
    )

    print(
        f"[*] Waiting {ECU_RECOVERY_DELAY} seconds "
        "for ECU recovery..."
    )

    time.sleep(
        ECU_RECOVERY_DELAY
    )

    drain_receive_buffer()

    # NONE means the previous diagnostic session is
    # unknown. The script cannot automatically restore
    # an unknown session.

    if session_id is None:

        print(
            "[!] Session selection is NONE."
        )

        print(
            "[!] The previous testing session cannot "
            "be restored automatically."
        )

        print(
            "[!] The ECU may now be in Default Session."
        )

        return True

    print(
        f"[*] Switching back to testing Session "
        f"0x{session_id:02X}..."
    )

    session_result = prepare_testing_session(
        session_id,
        logger,
        show_output=False
    )

    if session_result["entered"]:

        print(
            f"[+] Testing Session "
            f"0x{session_id:02X} restored."
        )

        return True

    if session_result["nrc"] is not None:

        nrc_name = NRC_NAMES.get(
            session_result["nrc"],
            "Unknown NRC"
        )

        print(
            f"[!] Unable to restore testing Session "
            f"0x{session_id:02X}."
        )

        print(
            f"[!] NRC "
            f"0x{session_result['nrc']:02X}: "
            f"{nrc_name}"
        )

    else:

        print(
            f"[!] Testing Session "
            f"0x{session_id:02X} was not restored."
        )

    return False


# ====================================================
# ECU Reset Type Scanner
# ====================================================

def scan_reset_types(
        session_id,
        logger):

    supported_reset_types = []

    print()
    print(
        f"Scanning ECU Reset subfunctions from "
        f"0x{RESET_SCAN_START:02X} to "
        f"0x{RESET_SCAN_END:02X}..."
    )

    # The testing session is entered before starting
    # this loop.
    #
    # The testing session is restored only after a
    # positive ECU Reset response.
    #
    # A final NRC does not trigger session restoration.

    for reset_type in range(
            RESET_SCAN_START,
            RESET_SCAN_END + 1):

        result = test_reset_type(
            reset_type,
            logger
        )

        # Execution reaches this section only after
        # a final positive or negative response.

        if result["positive_reset"]:

            supported_reset_types.append({
                "reset_type": reset_type,
                "classification":
                    result["classification"],
                "nrc": None
            })

            print(
                f"    [+] Reset Type "
                f"0x{reset_type:02X} supported"
            )

            print(
                "    [+] Positive response received"
            )

            # Restore the testing session only because
            # the ECU Reset request was accepted.

            restore_successful = (
                restore_session_after_positive_reset(
                    session_id,
                    logger
                )
            )

            if not restore_successful:

                print()
                print(
                    "[!] Testing session restoration "
                    "failed."
                )

                print(
                    "[!] Enumeration stopped to avoid "
                    "testing subsequent reset types in "
                    "the wrong session."
                )

                break

        elif result["nrc"] is not None:

            nrc = result["nrc"]

            nrc_name = NRC_NAMES.get(
                nrc,
                "Unknown NRC"
            )

            if result["supported"]:

                supported_reset_types.append({
                    "reset_type": reset_type,
                    "classification":
                        result["classification"],
                    "nrc": nrc
                })

                print(
                    f"    [+] Reset Type "
                    f"0x{reset_type:02X} recognised"
                )

                print(
                    f"    [+] Final NRC "
                    f"0x{nrc:02X}: {nrc_name}"
                )

            else:

                print(
                    f"    [-] Reset Type "
                    f"0x{reset_type:02X} not supported"
                )

                print(
                    f"    [-] Final NRC "
                    f"0x{nrc:02X}: {nrc_name}"
                )

            # A final NRC indicates that the reset was
            # not executed.
            #
            # Therefore, do not switch back to the
            # testing session.

            print(
                "    [*] Final NRC received."
            )

            print(
                "    [*] Testing session will not "
                "be switched."
            )

        else:

            print(
                f"    [-] Unclassified result for "
                f"Reset Type 0x{reset_type:02X}"
            )

        # Wait only after:
        #
        # 1. A final NRC has been received, or
        # 2. A positive response has been received and
        #    the testing session has been restored.

        if reset_type < RESET_SCAN_END:

            print(
                f"    [*] Waiting "
                f"{REQUEST_INTERVAL} seconds before "
                "the next ECU Reset request..."
            )

            time.sleep(
                REQUEST_INTERVAL
            )

    return supported_reset_types


# ====================================================
# Result Display
# ====================================================

def display_reset_results(
        session_id,
        reset_types):

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
        f"Enumerated ECU Reset Types for "
        f"{session_text}:"
    )
    print()

    print(
        "+------------+--------------------------------------+"
    )

    print(
        "| Reset Type | Description                          |"
    )

    print(
        "+------------+--------------------------------------+"
    )

    for result in reset_types:

        reset_type = result[
            "reset_type"
        ]

        description = ECU_RESET_TYPE_NAMES.get(
            reset_type,
            f"OEM Reset Type 0x{reset_type:02X}"
        )

        print(
            f"| 0x{reset_type:02X}       | "
            f"{description:<36} |"
        )

    print(
        "+------------+--------------------------------------+"
    )

    print(
        f"\nTotal recognised ECU Reset Types: "
        f"{len(reset_types)}"
    )


# ====================================================
# ASC Log Name
# ====================================================

def get_log_name(session_id):

    if session_id is None:

        return (
            "ECU_Reset_Enumeration_"
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
        f"ECU_Reset_Enumeration_"
        f"Session_{session_id:02X}_"
        f"{safe_session_name}"
    )


# ====================================================
# Scan One Diagnostic Session
# ====================================================

def scan_selected_session(session_id):

    logger = ASCLogger()

    log_name = get_log_name(
        session_id
    )

    reset_types = []
    session_ready = False

    print()
    print("=" * 64)

    if session_id is None:

        print(
            "Selected Session: NONE"
        )

        print(
            "Current active ECU session will be used."
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

        if session_id is None:

            session_ready = True

            print(
                "[*] No Diagnostic Session Control "
                "request will be sent."
            )

            print(
                "[!] After a positive ECU Reset, the "
                "ECU may return to Default Session."
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
                    f"[!] Testing Session "
                    f"0x{session_id:02X} was not confirmed."
                )

        if session_ready:

            reset_types = scan_reset_types(
                session_id,
                logger
            )

            display_reset_results(
                session_id,
                reset_types
            )

        else:

            print(
                "[!] ECU Reset enumeration skipped "
                "because the testing session could "
                "not be entered."
            )

    except KeyboardInterrupt:

        print()
        print(
            "[!] Session scan interrupted by user."
        )

        raise

    finally:

        # Request Default Session when finishing an
        # explicitly selected session.
        #
        # This final cleanup transition is independent
        # of scanning logic.
        #
        # NONE mode does not change diagnostic session.

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

        try:

            logger.stop_log()

            print(
                f"[+] ASC log closed: {log_name}"
            )

        except Exception as error:

            print(
                f"[!] ASC log close error: {error}"
            )

    return reset_types


# ====================================================
# Programme Start
# ====================================================

print()
print("==================================================")
print("          ECU Reset Type Enumeration Tool")
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

RESPONSE_POLL_TIMEOUT = get_float_input(
    "Enter ECU response polling timeout",
    DEFAULT_RESPONSE_POLL_TIMEOUT
)

REQUEST_INTERVAL = get_float_input(
    "Enter time between consecutive reset requests",
    DEFAULT_REQUEST_INTERVAL
)

ECU_RECOVERY_DELAY = get_float_input(
    "Enter ECU recovery delay after positive reset",
    DEFAULT_ECU_RECOVERY_DELAY
)

SESSION_SELECTION = get_session_selection()

SELECTED_SESSIONS = SESSION_SELECTION[
    "sessions"
]


# ====================================================
# Display Configuration
# ====================================================

print()
print("Selected Configuration")
print("--------------------------------------------------")
print(f"TX CAN ID          : 0x{TX_ID:X}")
print(f"RX CAN ID          : 0x{RX_ID:X}")
print(
    f"Response polling   : "
    f"{RESPONSE_POLL_TIMEOUT} seconds"
)
print(
    f"Request interval   : "
    f"{REQUEST_INTERVAL} seconds"
)
print(
    f"ECU recovery delay : "
    f"{ECU_RECOVERY_DELAY} seconds"
)
print(
    f"Reset scan range   : "
    f"0x{RESET_SCAN_START:02X} to "
    f"0x{RESET_SCAN_END:02X}"
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

    selected_session = SELECTED_SESSIONS[0]

    print(
        f"Session selection   : "
        f"0x{selected_session:02X}"
    )

print("--------------------------------------------------")


# ====================================================
# Execute ECU Reset Enumeration
# ====================================================

all_results = {}

try:

    bus = create_can_bus()

    print()
    print(
        "[*] Starting ECU Reset Type enumeration..."
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

        all_results[result_key] = {
            "session_id": selected_session,
            "reset_types": session_results
        }

except KeyboardInterrupt:

    print()
    print(
        "[!] ECU Reset enumeration stopped by user."
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

    # The CAN bus is shut down exactly once.
    #
    # It is not shut down inside a session loop or
    # reset-type loop.

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
print("ECU Reset Type Enumeration Completed")
print("=" * 64)

if not all_results:

    print(
        "No session scan was completed."
    )

else:

    for result_data in all_results.values():

        display_reset_results(
            result_data["session_id"],
            result_data["reset_types"]
        )