import time
import can

from ASC_Logger import ASCLogger


# ====================================================
# Vector CAN Interface Configuration
# ====================================================

CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"

CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000

USE_EXTENDED_CAN_ID = False


# ====================================================
# DID Enumeration Configuration
# ====================================================

DID_SCAN_START = 0xFE00
DID_SCAN_END = 0xFFFF

DEFAULT_RESPONSE_TIMEOUT = 0.50
DEFAULT_REQUEST_INTERVAL = 0.01

DEFAULT_SESSION_DELAY = 0.50
SESSION_ENTRY_DELAY = 0.50

# ISO-TP Flow Control parameters
#
# 0x00: Continue To Send
# Block Size 0 means that the ECU may send all
# Consecutive Frames without another Flow Control.
# STmin 0 means no additional separation delay is
# requested from the ECU.

FLOW_STATUS = 0x00
FLOW_CONTROL_BLOCK_SIZE = 0x00
FLOW_CONTROL_ST_MIN = 0x00


# ====================================================
# Diagnostic Session Definitions
# ====================================================

SESSION_NAMES = {
    0x01: "Default Session",
    0x02: "Programming Session",
    0x03: "Extended Session",
    0x04: "Safety System Session"
}


# Sessions enumerated when ALL is selected.
#
# Add confirmed OEM-specific sessions when required.
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
# NRC Definitions
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
# Runtime Objects
# ====================================================

bus = None

TX_ID = None
RX_ID = None

RESPONSE_TIMEOUT = None
REQUEST_INTERVAL = None

TRANSMIT_CAN_FD = False
TRANSMIT_PADDING_LENGTH = 8


# ====================================================
# User Input Helpers
# ====================================================

def get_hex_input(prompt, default, minimum=None, maximum=None):

    while True:

        value = input(
            f"{prompt} (default 0x{default:X}): "
        ).strip()

        if value == "":
            converted_value = default

        else:

            try:
                converted_value = int(value, 16)

            except ValueError:

                print("[!] Invalid hexadecimal value.")
                print("    Examples: 471, 0x471, 7E0")
                continue

        if minimum is not None and converted_value < minimum:

            print(
                f"[!] Value must be at least "
                f"0x{minimum:X}."
            )

            continue

        if maximum is not None and converted_value > maximum:

            print(
                f"[!] Value must not exceed "
                f"0x{maximum:X}."
            )

            continue

        return converted_value


def get_float_input(
        prompt,
        default,
        allow_zero=False):

    while True:

        value = input(
            f"{prompt} (default {default} seconds): "
        ).strip()

        if value == "":
            return default

        try:

            converted_value = float(value)

            if allow_zero:

                if converted_value < 0:
                    raise ValueError

            elif converted_value <= 0:

                raise ValueError

            return converted_value

        except ValueError:

            if allow_zero:

                print(
                    "[!] Enter a numeric value equal "
                    "to or greater than zero."
                )

            else:

                print(
                    "[!] Enter a numeric value greater "
                    "than zero."
                )


def get_yes_no_input(prompt, default=False):

    default_text = "Y" if default else "N"

    while True:

        value = input(
            f"{prompt} (Y/N, default {default_text}): "
        ).strip().upper()

        if value == "":
            return default

        if value in {"Y", "YES"}:
            return True

        if value in {"N", "NO"}:
            return False

        print("[!] Enter Y or N.")


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
        fd=True,
        bitrate=CAN_BITRATE,
        dbitrate=CAN_DATA_BITRATE,
        receive_own_messages=True
    )

    print("[+] Vector CAN interface opened.")

    return created_bus


# ====================================================
# CAN DLC Padding Helpers
# ====================================================

def get_valid_can_fd_length(required_length):

    valid_lengths = [
        8,
        12,
        16,
        20,
        24,
        32,
        48,
        64
    ]

    for valid_length in valid_lengths:

        if required_length <= valid_length:
            return valid_length

    raise ValueError(
        "CAN FD payload length cannot exceed 64 bytes."
    )


def pad_frame_data(frame_data, target_length):

    padded_data = list(frame_data)

    while len(padded_data) < target_length:

        padded_data.append(0x00)

    return padded_data


# ====================================================
# ISO-TP Request Creation
# ====================================================

def create_isotp_single_frame(payload):

    payload_length = len(payload)

    if payload_length == 0:

        raise ValueError(
            "UDS payload cannot be empty."
        )

    # ------------------------------------------------
    # Classic CAN ISO-TP Single Frame
    #
    # Byte 0:
    #     High nibble = 0
    #     Low nibble  = payload length
    #
    # Used for payloads from 1 to 7 bytes.
    # ------------------------------------------------

    if not TRANSMIT_CAN_FD:

        if payload_length > 7:

            raise ValueError(
                "Classic CAN ISO-TP Single Frame "
                "cannot contain more than seven "
                "UDS payload bytes."
            )

        frame_data = [
            payload_length
        ]

        frame_data.extend(payload)

        return pad_frame_data(
            frame_data,
            8
        )

    # ------------------------------------------------
    # CAN FD ISO-TP Single Frame
    #
    # For a payload length up to 7 bytes, normal
    # Single Frame encoding is valid.
    #
    # For a payload length above 7 bytes, CAN FD
    # ISO-TP escape-length encoding is used:
    #
    #     00 <payload length> <payload>
    # ------------------------------------------------

    if payload_length <= 7:

        frame_data = [
            payload_length
        ]

        frame_data.extend(payload)

    else:

        if payload_length > 62:

            raise ValueError(
                "CAN FD ISO-TP Single Frame payload "
                "cannot exceed 62 bytes when escape "
                "length encoding is used."
            )

        frame_data = [
            0x00,
            payload_length
        ]

        frame_data.extend(payload)

    target_length = get_valid_can_fd_length(
        max(
            len(frame_data),
            TRANSMIT_PADDING_LENGTH
        )
    )

    return pad_frame_data(
        frame_data,
        target_length
    )


# ====================================================
# ASC Logging Helper
# ====================================================

def log_tx_message(message, logger):

    if not getattr(
            message,
            "timestamp",
            None
    ):

        message.timestamp = time.time()

    logger.log_frame(
        message,
        "Tx"
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


def send_uds_request(payload, logger):

    frame_data = create_isotp_single_frame(
        payload
    )

    message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=USE_EXTENDED_CAN_ID,
        is_fd=TRANSMIT_CAN_FD,
        bitrate_switch=TRANSMIT_CAN_FD,
        data=frame_data
    )

    bus.send(message)

    pass


# ====================================================
# ISO-TP Flow Control
# ====================================================

def send_flow_control(
        received_first_frame,
        logger):

    flow_control_data = [
        0x30 | FLOW_STATUS,
        FLOW_CONTROL_BLOCK_SIZE,
        FLOW_CONTROL_ST_MIN
    ]

    # Use the same transport type as the received
    # First Frame.
    #
    # Classic CAN:
    #     Pad Flow Control to 8 bytes.
    #
    # CAN FD:
    #     Use a valid CAN FD frame length.

    if received_first_frame.is_fd:

        target_length = get_valid_can_fd_length(
            max(
                8,
                len(flow_control_data)
            )
        )

    else:

        target_length = 8

    flow_control_data = pad_frame_data(
        flow_control_data,
        target_length
    )

    flow_control_message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=USE_EXTENDED_CAN_ID,
        is_fd=received_first_frame.is_fd,
        bitrate_switch=(
            received_first_frame.bitrate_switch
            if received_first_frame.is_fd
            else False
        ),
        data=flow_control_data
    )

    bus.send(
        flow_control_message
    )

    pass


# ====================================================
# ISO-TP Frame Parsing
# ====================================================

def parse_isotp_frame(message):

    data = bytes(message.data)

    if len(data) == 0:
        return None

    pci_type = (
        data[0] >> 4
    )

    # ------------------------------------------------
    # Single Frame
    # ------------------------------------------------

    if pci_type == 0x00:

        normal_length = (
            data[0] & 0x0F
        )

        # Normal Single Frame length encoding

        if normal_length != 0:

            if normal_length > len(data) - 1:
                return None

            return {
                "type": "single",
                "payload": bytes(
                    data[
                        1:1 + normal_length
                    ]
                )
            }

        # CAN FD escape length encoding:
        #
        # Byte 0 = 0x00
        # Byte 1 = actual payload length

        if len(data) < 2:
            return None

        escape_length = data[1]

        if escape_length == 0:
            return None

        if escape_length > len(data) - 2:
            return None

        return {
            "type": "single",
            "payload": bytes(
                data[
                    2:2 + escape_length
                ]
            )
        }

    # ------------------------------------------------
    # First Frame
    # ------------------------------------------------

    if pci_type == 0x01:

        if len(data) < 2:
            return None

        normal_total_length = (
            (
                data[0] & 0x0F
            ) << 8
        ) | data[1]

        # Normal 12-bit First Frame length

        if normal_total_length != 0:

            return {
                "type": "first",
                "total_length":
                    normal_total_length,
                "payload": bytes(
                    data[2:]
                )
            }

        # Extended First Frame length encoding:
        #
        # Byte 0 and Byte 1 contain zero length.
        # Bytes 2 to 5 contain a 32-bit length.

        if len(data) < 6:
            return None

        extended_total_length = int.from_bytes(
            data[2:6],
            byteorder="big",
            signed=False
        )

        if extended_total_length == 0:
            return None

        return {
            "type": "first",
            "total_length":
                extended_total_length,
            "payload": bytes(
                data[6:]
            )
        }

    # ------------------------------------------------
    # Consecutive Frame
    # ------------------------------------------------

    if pci_type == 0x02:

        sequence_number = (
            data[0] & 0x0F
        )

        return {
            "type": "consecutive",
            "sequence_number":
                sequence_number,
            "payload": bytes(
                data[1:]
            )
        }

    # ------------------------------------------------
    # Flow Control
    # ------------------------------------------------

    if pci_type == 0x03:

        return {
            "type": "flow_control",
            "flow_status":
                data[0] & 0x0F
        }

    return {
        "type": "unknown"
    }


# ====================================================
# Generic ISO-TP Response Receiver
# ====================================================

def receive_complete_isotp_payload(
        logger,
        wait_indefinitely_after_pending=False):

    deadline = (
        time.monotonic()
        + RESPONSE_TIMEOUT
    )

    response_pending_received = False

    reassembly_active = False
    expected_total_length = 0
    expected_sequence_number = 1
    reassembly_buffer = bytearray()

    while True:

        # Before NRC 0x78 or a multi-frame First Frame,
        # the configured response timeout is enforced.
        #
        # After NRC 0x78 or a First Frame, the scanner
        # waits for completion and refreshes the
        # deadline whenever another valid response
        # frame is received.

        remaining_time = (
            deadline
            - time.monotonic()
        )

        if remaining_time <= 0:

            if (
                wait_indefinitely_after_pending
                and response_pending_received
            ):

                deadline = (
                    time.monotonic()
                    + RESPONSE_TIMEOUT
                )

                continue

            return {
                "status": "timeout",
                "payload": None,
                "response_pending":
                    response_pending_received,
                "transport":
                    (
                        "multi-frame"
                        if reassembly_active
                        else None
                    )
            }

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

        parsed_frame = parse_isotp_frame(
            message
        )

        if parsed_frame is None:
            continue

        frame_type = parsed_frame[
            "type"
        ]

        # ------------------------------------------------
        # Complete Single Frame response
        # ------------------------------------------------

        if frame_type == "single":

            payload = parsed_frame[
                "payload"
            ]

            # NRC 0x78 is an intermediate response.
            #
            # Return it to the UDS-level handler so the
            # receiver can continue waiting for the
            # final response.

            return {
                "status": "complete",
                "payload": payload,
                "response_pending":
                    response_pending_received,
                "transport":
                    (
                        "can-fd-single-frame"
                        if message.is_fd
                        else "can-single-frame"
                    ),
                "is_fd": message.is_fd
            }

        # ------------------------------------------------
        # ISO-TP First Frame
        # ------------------------------------------------

        if frame_type == "first":

            expected_total_length = (
                parsed_frame[
                    "total_length"
                ]
            )

            reassembly_buffer = bytearray(
                parsed_frame[
                    "payload"
                ]
            )

            expected_sequence_number = 1
            reassembly_active = True

            send_flow_control(
                message,
                logger
            )

            deadline = (
                time.monotonic()
                + RESPONSE_TIMEOUT
            )

            if (
                len(reassembly_buffer)
                >= expected_total_length
            ):

                complete_payload = bytes(
                    reassembly_buffer[
                        :expected_total_length
                    ]
                )

                return {
                    "status": "complete",
                    "payload":
                        complete_payload,
                    "response_pending":
                        response_pending_received,
                    "transport":
                        (
                            "can-fd-isotp"
                            if message.is_fd
                            else "can-isotp"
                        ),
                    "is_fd": message.is_fd
                }

            continue

        # ------------------------------------------------
        # ISO-TP Consecutive Frame
        # ------------------------------------------------

        if frame_type == "consecutive":

            if not reassembly_active:
                continue

            received_sequence_number = (
                parsed_frame[
                    "sequence_number"
                ]
            )

            if (
                received_sequence_number
                != expected_sequence_number
            ):

                return {
                    "status":
                        "sequence_error",
                    "payload": None,
                    "expected_sequence":
                        expected_sequence_number,
                    "received_sequence":
                        received_sequence_number,
                    "response_pending":
                        response_pending_received,
                    "transport":
                        (
                            "can-fd-isotp"
                            if message.is_fd
                            else "can-isotp"
                        )
                }

            reassembly_buffer.extend(
                parsed_frame[
                    "payload"
                ]
            )

            expected_sequence_number = (
                expected_sequence_number + 1
            ) & 0x0F

            deadline = (
                time.monotonic()
                + RESPONSE_TIMEOUT
            )

            if (
                len(reassembly_buffer)
                >= expected_total_length
            ):

                complete_payload = bytes(
                    reassembly_buffer[
                        :expected_total_length
                    ]
                )

                return {
                    "status": "complete",
                    "payload":
                        complete_payload,
                    "response_pending":
                        response_pending_received,
                    "transport":
                        (
                            "can-fd-isotp"
                            if message.is_fd
                            else "can-isotp"
                        ),
                    "is_fd": message.is_fd
                }

            continue


# ====================================================
# Receive Final UDS Response
# ====================================================

def receive_final_uds_response(
        expected_service,
        logger):

    response_pending_seen = False

    while True:

        transport_result = (
            receive_complete_isotp_payload(
                logger,
                wait_indefinitely_after_pending=(
                    response_pending_seen
                )
            )
        )

        if transport_result["status"] != "complete":

            return {
                "status":
                    transport_result["status"],
                "payload": None,
                "transport":
                    transport_result.get(
                        "transport"
                    ),
                "response_pending":
                    response_pending_seen
            }

        payload = transport_result[
            "payload"
        ]

        if payload is None or len(payload) == 0:
            continue

        # Ignore unrelated positive responses.

        expected_positive_service = (
            expected_service + 0x40
        )

        if payload[0] == expected_positive_service:

            return {
                "status": "positive",
                "payload": payload,
                "transport":
                    transport_result[
                        "transport"
                    ],
                "response_pending":
                    response_pending_seen
            }

        # Negative response:
        #
        # 7F <requested SID> <NRC>

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1] == expected_service
        ):

            nrc = payload[2]

            if nrc == 0x78:

                response_pending_seen = True

                print(
                    "    [*] NRC 0x78 received. "
                    "Waiting for final response..."
                )

                continue

            return {
                "status": "negative",
                "payload": payload,
                "nrc": nrc,
                "transport":
                    transport_result[
                        "transport"
                    ],
                "response_pending":
                    response_pending_seen
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

    response = receive_final_uds_response(
        0x10,
        logger
    )

    if response["status"] == "positive":

        payload = response["payload"]

        if (
            len(payload) >= 2
            and payload[0] == 0x50
            and (
                payload[1] & 0x7F
            ) == (
                session_id & 0x7F
            )
        ):

            time.sleep(
                SESSION_ENTRY_DELAY
            )

            return {
                "entered": True,
                "nrc": None,
                "transport":
                    response["transport"]
            }

    if response["status"] == "negative":

        return {
            "entered": False,
            "nrc": response["nrc"],
            "transport":
                response["transport"]
        }

    return {
        "entered": False,
        "nrc": None,
        "transport":
            response.get(
                "transport"
            )
    }


def prepare_testing_session(
        session_id,
        logger,
        show_output=True):

    if session_id is None:

        return {
            "entered": True,
            "nrc": None
        }

    # Before entering a non-default session,
    # request Default Session first.

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
                        "[!] Default Session response "
                        "was not confirmed."
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
# ReadDataByIdentifier Request
# ====================================================

def request_did(
        did,
        logger):

    did_high = (
        did >> 8
    ) & 0xFF

    did_low = (
        did & 0xFF
    )

    drain_receive_buffer()

    send_uds_request(
        [
            0x22,
            did_high,
            did_low
        ],
        logger
    )

    response = receive_final_uds_response(
        0x22,
        logger
    )

    # ------------------------------------------------
    # Positive response:
    #
    # 62 <DID High> <DID Low> <DID data>
    #
    # A positive response may use:
    #
    # - Classic CAN ISO-TP Single Frame
    # - Classic CAN ISO-TP Multi-Frame
    # - CAN FD ISO-TP Single Frame
    # - CAN FD ISO-TP Multi-Frame
    # ------------------------------------------------

    if response["status"] == "positive":

        payload = response["payload"]

        if (
            len(payload) >= 3
            and payload[0] == 0x62
            and payload[1] == did_high
            and payload[2] == did_low
        ):

            did_data = bytes(
                payload[3:]
            )

            return {
                "supported": True,
                "classification":
                    "Positive Response",
                "nrc": None,
                "data_length":
                    len(did_data),
                "transport":
                    response["transport"],
                "payload": payload
            }

        return {
            "supported": False,
            "classification":
                "Positive Response DID Mismatch",
            "nrc": None,
            "data_length": 0,
            "transport":
                response["transport"],
            "payload": payload
        }

    # ------------------------------------------------
    # Final negative response
    # ------------------------------------------------

    if response["status"] == "negative":

        return {
            "supported": False,
            "classification":
                "Negative Response",
            "nrc":
                response["nrc"],
            "data_length": 0,
            "transport":
                response["transport"],
            "payload":
                response["payload"]
        }

    # ------------------------------------------------
    # Timeout or ISO-TP error
    # ------------------------------------------------

    return {
        "supported": False,
        "classification":
            response["status"],
        "nrc": None,
        "data_length": 0,
        "transport":
            response.get(
                "transport"
            ),
        "payload": None
    }


# ====================================================
# Enumeration Progress Display
# ====================================================

def print_progress(
        processed,
        total,
        current_did,
        supported_count):

    percentage = (
        processed / total
    ) * 100.0

    print(
        f"\r"
        f"Processed: {processed:5}/{total} "
        f"({percentage:6.2f}%) | "
        f"Current DID: 0x{current_did:04X} | "
        f"Supported: {supported_count}",
        end="",
        flush=True
    )


# ====================================================
# DID Scanner
# ====================================================

def scan_dids(
        session_id,
        logger):

    supported_dids = []

    statistics = {
        "processed": 0,
        "supported": 0,
        "unsupported": 0,
        "no_response": 0,
        "nrc_11": 0,
        "nrc_13": 0,
        "nrc_22": 0,
        "nrc_31": 0,
        "nrc_33": 0,
        "nrc_7e": 0,
        "nrc_7f": 0,
        "other_nrc": 0,
        "transport_error": 0
    }

    total_requests = (
        DID_SCAN_END
        - DID_SCAN_START
        + 1
    )

    print()
    print(
        f"Scanning DIDs from "
        f"0x{DID_SCAN_START:04X} to "
        f"0x{DID_SCAN_END:04X}..."
    )

    print()

    for did in range(
            DID_SCAN_START,
            DID_SCAN_END + 1):

        result = request_did(
            did,
            logger
        )

        statistics["processed"] += 1

        if result["supported"]:

            statistics["supported"] += 1

            supported_dids.append({
                "did": did,
                "data_length":
                    result["data_length"],
                "transport":
                    result["transport"]
            })

            # Print a separate line immediately when
            # a supported DID is discovered.

            print()

            print(
                f"[+] Supported DID: "
                f"0x{did:04X} | "
                f"Data length: "
                f"{result['data_length']} byte(s) | "
                f"Transport: "
                f"{result['transport']}"
            )

        else:

            statistics["unsupported"] += 1

            nrc = result["nrc"]

            if nrc is not None:

                if nrc == 0x11:
                    statistics["nrc_11"] += 1

                elif nrc == 0x13:
                    statistics["nrc_13"] += 1

                elif nrc == 0x22:
                    statistics["nrc_22"] += 1

                elif nrc == 0x31:
                    statistics["nrc_31"] += 1

                elif nrc == 0x33:
                    statistics["nrc_33"] += 1

                elif nrc == 0x7E:
                    statistics["nrc_7e"] += 1

                elif nrc == 0x7F:
                    statistics["nrc_7f"] += 1

                else:
                    statistics["other_nrc"] += 1

            elif result["classification"] == "timeout":

                statistics["no_response"] += 1

            else:

                statistics["transport_error"] += 1

        print_progress(
            statistics["processed"],
            total_requests,
            did,
            statistics["supported"]
        )

        # Time between consecutive DID requests.
        #
        # This delay starts only after response
        # processing for the previous request has
        # completed.

        if did < DID_SCAN_END:

            time.sleep(
                REQUEST_INTERVAL
            )

    print()

    return {
        "supported_dids": supported_dids,
        "statistics": statistics
    }


# ====================================================
# DID Grid Display
# ====================================================

def display_did_grid(
        supported_dids,
        columns=10):

    print()
    print(
        "Enumerated Read Identifiers (DID):"
    )
    print()

    if not supported_dids:

        print(
            "No DIDs returned a matching positive "
            "0x62 response."
        )

        return

    did_values = [
        result["did"]
        for result in supported_dids
    ]

    cell_width = 8

    horizontal_line = (
        "+"
        + "+".join(
            "-" * cell_width
            for _ in range(columns)
        )
        + "+"
    )

    for row_start in range(
            0,
            len(did_values),
            columns):

        row = did_values[
            row_start:
            row_start + columns
        ]

        print(horizontal_line)

        cells = []

        for did in row:

            cells.append(
                f"{did:04X}".center(
                    cell_width
                )
            )

        while len(cells) < columns:

            cells.append(
                " " * cell_width
            )

        print(
            "|"
            + "|".join(cells)
            + "|"
        )

    print(horizontal_line)


# ====================================================
# Enumeration Summary Display
# ====================================================

def display_did_results(
        session_id,
        result):

    statistics = result[
        "statistics"
    ]

    supported_dids = result[
        "supported_dids"
    ]

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

    separator = "=" * 100

    print()
    print(separator)
    print(
        "READ DATA BY IDENTIFIER (0x22) "
        "ENUMERATION SUMMARY".center(100)
    )
    print(
        session_text.center(100)
    )
    print(separator)

    print(
        f"Total DID Requests Processed       : "
        f"{statistics['processed']}"
    )

    print(
        f"Total Unsupported DIDs             : "
        f"{statistics['unsupported']}"
    )

    print(
        f"Total Supported DIDs Discovered    : "
        f"{statistics['supported']}"
    )

    print(
        f"Total No-Response DIDs             : "
        f"{statistics['no_response']}"
    )

    print(
        f"Total NRC 0x11 Responses           : "
        f"{statistics['nrc_11']}"
    )

    print(
        f"Total NRC 0x13 Responses           : "
        f"{statistics['nrc_13']}"
    )

    print(
        f"Total NRC 0x22 Responses           : "
        f"{statistics['nrc_22']}"
    )

    print(
        f"Total NRC 0x31 Responses           : "
        f"{statistics['nrc_31']}"
    )

    print(
        f"Total NRC 0x33 Responses           : "
        f"{statistics['nrc_33']}"
    )

    print(
        f"Total NRC 0x7E Responses           : "
        f"{statistics['nrc_7e']}"
    )

    print(
        f"Total NRC 0x7F Responses           : "
        f"{statistics['nrc_7f']}"
    )

    print(
        f"Total Other NRC Responses          : "
        f"{statistics['other_nrc']}"
    )

    print(
        f"Total ISO-TP/Transport Errors       : "
        f"{statistics['transport_error']}"
    )

    print(separator)

    display_did_grid(
        supported_dids,
        columns=10
    )


# ====================================================
# ASC Log Name
# ====================================================

def get_log_name(session_id):

    if session_id is None:

        return (
            "Read_DID_Enumeration_"
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
        f"Read_DID_Enumeration_"
        f"Session_{session_id:02X}_"
        f"{safe_session_name}"
    )


# ====================================================
# Empty Session Result
# ====================================================

def create_empty_result():

    return {
        "supported_dids": [],
        "statistics": {
            "processed": 0,
            "supported": 0,
            "unsupported": 0,
            "no_response": 0,
            "nrc_11": 0,
            "nrc_13": 0,
            "nrc_22": 0,
            "nrc_31": 0,
            "nrc_33": 0,
            "nrc_7e": 0,
            "nrc_7f": 0,
            "other_nrc": 0,
            "transport_error": 0
        }
    }


# ====================================================
# Scan One Diagnostic Session
# ====================================================

def scan_selected_session(session_id):

    logger = ASCLogger()

    log_name = get_log_name(
        session_id
    )

    result = create_empty_result()

    session_ready = False
    log_started = False

    print()
    print("=" * 100)

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

    print("=" * 100)

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

            result = scan_dids(
                session_id,
                logger
            )

            # Print the output immediately after
            # completing this session.

            display_did_results(
                session_id,
                result
            )

        else:

            print(
                "[!] DID enumeration skipped because "
                "the selected diagnostic session "
                "could not be entered."
            )

    except KeyboardInterrupt:

        print()
        print(
            "[!] DID enumeration interrupted by user."
        )

        raise

    finally:

        # Return the ECU to Default Session after an
        # explicitly selected session.
        #
        # NONE mode does not change the session.

        if (
            session_id is not None
            and session_ready
            and bus is not None
            and log_started
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

    return result


# ====================================================
# Programme Start
# ====================================================

print()
print("==================================================")
print("   Read Data By Identifier Enumeration Tool")
print("==================================================")
print()

TX_ID = get_hex_input(
    "Enter TX CAN ID",
    0x471,
    minimum=0x000,
    maximum=0x1FFFFFFF
)

RX_ID = get_hex_input(
    "Enter RX CAN ID",
    0x479,
    minimum=0x000,
    maximum=0x1FFFFFFF
)

RESPONSE_TIMEOUT = get_float_input(
    "Enter maximum response timeout for each DID",
    DEFAULT_RESPONSE_TIMEOUT
)

REQUEST_INTERVAL = get_float_input(
    "Enter time between consecutive DID requests",
    DEFAULT_REQUEST_INTERVAL,
    allow_zero=True
)

TRANSMIT_CAN_FD = get_yes_no_input(
    "Transmit diagnostic requests as CAN FD frames",
    default=False
)

if TRANSMIT_CAN_FD:

    TRANSMIT_PADDING_LENGTH = 8

else:

    TRANSMIT_PADDING_LENGTH = 8

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
    f"Extended CAN ID    : "
    f"{USE_EXTENDED_CAN_ID}"
)

print(
    f"Transmit mode      : "
    f"{'CAN FD' if TRANSMIT_CAN_FD else 'Classic CAN'}"
)

print(
    f"Response timeout   : "
    f"{RESPONSE_TIMEOUT} seconds"
)

print(
    f"Request interval   : "
    f"{REQUEST_INTERVAL} seconds"
)

print(
    f"DID scan range     : "
    f"0x{DID_SCAN_START:04X} to "
    f"0x{DID_SCAN_END:04X}"
)

print(
    f"Total DIDs/session : "
    f"{DID_SCAN_END - DID_SCAN_START + 1}"
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
# Execute DID Enumeration
# ====================================================

all_results = {}

try:

    bus = create_can_bus()

    print()
    print(
        "[*] Starting ReadDataByIdentifier "
        "enumeration..."
    )

    for selected_session in SELECTED_SESSIONS:

        session_result = scan_selected_session(
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
            "result": session_result
        }

except KeyboardInterrupt:

    print()
    print(
        "[!] DID enumeration stopped by user."
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
    # The CAN bus is not shut down inside the DID
    # loop or diagnostic-session loop.

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
# Final Summary
# ====================================================

print()
print("=" * 100)
print(
    "READ DATA BY IDENTIFIER ENUMERATION COMPLETED"
    .center(100)
)
print("=" * 100)

if not all_results:

    print(
        "No diagnostic-session scan was completed."
    )

else:

    for result_data in all_results.values():

        display_did_results(
            result_data["session_id"],
            result_data["result"]
        )