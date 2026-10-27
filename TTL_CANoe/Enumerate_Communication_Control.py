import time
import can
from ASC_Logger import ASCLogger

# ============================================================
# Vector CAN configuration
# ============================================================
CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"
CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000
USE_EXTENDED_CAN_ID = False

# ============================================================
# UDS CommunicationControl (0x28) configuration
# ============================================================
SERVICE_ID = 0x28
POSITIVE_RESPONSE_ID = 0x68
COMMUNICATION_TYPE = 0x01
SUBFUNCTION_SCAN_START = 0x00
SUBFUNCTION_SCAN_END = 0x7F

DEFAULT_RESPONSE_TIMEOUT = 0.50
DEFAULT_REQUEST_INTERVAL = 0.01
DEFAULT_SESSION_DELAY = 0.50
SESSION_ENTRY_DELAY = 0.50

FLOW_CONTROL_BLOCK_SIZE = 0x00
FLOW_CONTROL_ST_MIN = 0x00

SESSION_NAMES = {
    0x01: "Default Session",
    0x02: "Programming Session",
    0x03: "Extended Session",
    0x04: "Safety System Session",
}
ALL_SESSIONS = [0x01, 0x02, 0x03]

NRC_NAMES = {
    0x10: "General Reject",
    0x11: "Service Not Supported",
    0x12: "Sub-function Not Supported",
    0x13: "Incorrect Message Length Or Invalid Format",
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
    0x78: "Response Pending",
    0x7E: "Sub-function Not Supported In Active Session",
    0x7F: "Service Not Supported In Active Session",
}

# Requested reporting rule: NRC 0x33 proves that the subfunction is
# recognised by the ECU, even though access is currently denied.
SUPPORTED_NRC_CODES = {0x33}

bus = None
TX_ID = None
RX_ID = None
RESPONSE_TIMEOUT = DEFAULT_RESPONSE_TIMEOUT
REQUEST_INTERVAL = DEFAULT_REQUEST_INTERVAL
TRANSMIT_CAN_FD = False


# ============================================================
# User input helpers
# ============================================================
def get_hex_input(prompt, default, minimum=0, maximum=0x1FFFFFFF):
    while True:
        raw = input(f"{prompt} (default 0x{default:X}): ").strip()
        try:
            value = default if raw == "" else int(raw, 16)
            if not minimum <= value <= maximum:
                raise ValueError
            return value
        except ValueError:
            print(f"[!] Enter a hexadecimal value from 0x{minimum:X} to 0x{maximum:X}.")


def get_float_input(prompt, default, allow_zero=False):
    while True:
        raw = input(f"{prompt} (default {default} seconds): ").strip()
        try:
            value = default if raw == "" else float(raw)
            if value < 0 or (value == 0 and not allow_zero):
                raise ValueError
            return value
        except ValueError:
            condition = "equal to or greater than zero" if allow_zero else "greater than zero"
            print(f"[!] Enter a numeric value {condition}.")


def get_yes_no_input(prompt, default=False):
    default_text = "Y" if default else "N"
    while True:
        raw = input(f"{prompt} (Y/N, default {default_text}): ").strip().upper()
        if raw == "":
            return default
        if raw in {"Y", "YES"}:
            return True
        if raw in {"N", "NO"}:
            return False
        print("[!] Enter Y or N.")


def get_session_selection():
    print("\n============================================================")
    print("Diagnostic Session Selection")
    print("============================================================")
    print("  01    Default Session")
    print("  02    Programming Session")
    print("  03    Extended Session")
    print("  04    Safety System Session")
    print("  ALL   Scan all configured sessions one after another")
    print("  NONE  Scan the ECU's currently active session")
    print("============================================================")

    while True:
        raw = input("Select 0x01, 0x02, 0x03, 0x04, ALL, or NONE: ").strip()
        upper = raw.upper()
        if upper == "ALL":
            return {"mode": "ALL", "sessions": ALL_SESSIONS.copy()}
        if upper == "NONE":
            return {"mode": "NONE", "sessions": [None]}
        try:
            session_id = int(raw, 16)
            if not 0x00 <= session_id <= 0x7F:
                raise ValueError
            return {"mode": "SINGLE", "sessions": [session_id]}
        except ValueError:
            print("[!] Enter one hexadecimal session ID, ALL, or NONE.")


# ============================================================
# CAN and ISO-TP helpers
# ============================================================
def create_can_bus():
    print("[*] Opening Vector CAN interface...")
    created_bus = can.Bus(
        interface=CAN_INTERFACE,
        channel=CAN_CHANNEL,
        app_name=CAN_APP_NAME,
        fd=True,
        bitrate=CAN_BITRATE,
        dbitrate=CAN_DATA_BITRATE,
        receive_own_messages=True,
    )
    print("[+] Vector CAN interface opened.")
    return created_bus


def get_can_fd_length(required_length):
    for length in (8, 12, 16, 20, 24, 32, 48, 64):
        if required_length <= length:
            return length
    raise ValueError("CAN FD frame length exceeds 64 bytes.")


def pad_frame(data, target_length):
    data = list(data)
    return data + [0x00] * (target_length - len(data))


def create_isotp_single_frame(payload, use_can_fd=None):
    if not payload:
        raise ValueError("UDS payload cannot be empty.")

    is_fd = TRANSMIT_CAN_FD if use_can_fd is None else use_can_fd
    if not is_fd:
        if len(payload) > 7:
            raise ValueError("Classic CAN ISO-TP Single Frame supports at most 7 UDS bytes.")
        return pad_frame([len(payload)] + list(payload), 8)

    if len(payload) <= 7:
        raw = [len(payload)] + list(payload)
    else:
        if len(payload) > 62:
            raise ValueError("CAN FD ISO-TP Single Frame supports at most 62 UDS bytes.")
        raw = [0x00, len(payload)] + list(payload)
    return pad_frame(raw, get_can_fd_length(max(8, len(raw))))


def log_tx(message, logger):
    if not getattr(message, "timestamp", None):
        message.timestamp = time.time()
    logger.log_frame(message, "Tx")


def send_uds_request(payload, logger):
    message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=USE_EXTENDED_CAN_ID,
        is_fd=TRANSMIT_CAN_FD,
        bitrate_switch=TRANSMIT_CAN_FD,
        data=create_isotp_single_frame(payload),
    )
    bus.send(message)
    pass


def drain_receive_buffer():
    if bus is None:
        return
    while bus.recv(timeout=0.001) is not None:
        pass


def send_flow_control(first_frame, logger):
    # Continue To Send, unlimited block size, configured STmin.
    fc_data = pad_frame(
        [0x30, FLOW_CONTROL_BLOCK_SIZE, FLOW_CONTROL_ST_MIN],
        8,
    )
    message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=USE_EXTENDED_CAN_ID,
        is_fd=first_frame.is_fd,
        bitrate_switch=(first_frame.bitrate_switch if first_frame.is_fd else False),
        data=fc_data,
    )
    bus.send(message)
    pass


def parse_isotp_frame(message):
    data = bytes(message.data)
    if not data:
        return None

    pci_type = data[0] >> 4

    # Single Frame, including CAN FD escape-length Single Frame.
    if pci_type == 0x00:
        payload_length = data[0] & 0x0F
        offset = 1
        if payload_length == 0:
            if len(data) < 2 or data[1] == 0:
                return None
            payload_length = data[1]
            offset = 2
        if payload_length > len(data) - offset:
            return None
        return {
            "type": "single",
            "payload": data[offset:offset + payload_length],
        }

    # First Frame, including extended 32-bit ISO-TP length.
    if pci_type == 0x01:
        if len(data) < 2:
            return None
        total_length = ((data[0] & 0x0F) << 8) | data[1]
        offset = 2
        if total_length == 0:
            if len(data) < 6:
                return None
            total_length = int.from_bytes(data[2:6], "big")
            offset = 6
        if total_length == 0:
            return None
        return {
            "type": "first",
            "total_length": total_length,
            "payload": data[offset:],
        }

    if pci_type == 0x02:
        return {
            "type": "consecutive",
            "sequence_number": data[0] & 0x0F,
            "payload": data[1:],
        }

    if pci_type == 0x03:
        return {"type": "flow_control"}

    return {"type": "unknown"}


def receive_complete_isotp_payload(logger):
    deadline = time.monotonic() + RESPONSE_TIMEOUT
    reassembly_buffer = bytearray()
    total_length = None
    expected_sequence_number = 1
    transport = None

    while time.monotonic() < deadline:
        remaining = max(0.0, deadline - time.monotonic())
        message = bus.recv(timeout=min(0.01, remaining))
        if message is None:
            continue

        # Keep all received traffic in the ASC log, but process only RX_ID.
        logger.log_frame(message, "Rx")
        if message.arbitration_id != RX_ID:
            continue

        parsed = parse_isotp_frame(message)
        if not parsed:
            continue

        if parsed["type"] == "single":
            return {
                "status": "complete",
                "payload": parsed["payload"],
                "transport": (
                    "CAN FD ISO-TP Single Frame"
                    if message.is_fd
                    else "Classic CAN ISO-TP Single Frame"
                ),
            }

        if parsed["type"] == "first":
            total_length = parsed["total_length"]
            reassembly_buffer = bytearray(parsed["payload"])
            expected_sequence_number = 1
            transport = (
                "CAN FD ISO-TP Multi-Frame"
                if message.is_fd
                else "Classic CAN ISO-TP Multi-Frame"
            )
            send_flow_control(message, logger)
            deadline = time.monotonic() + RESPONSE_TIMEOUT
            if len(reassembly_buffer) >= total_length:
                return {
                    "status": "complete",
                    "payload": bytes(reassembly_buffer[:total_length]),
                    "transport": transport,
                }
            continue

        if parsed["type"] == "consecutive" and total_length is not None:
            if parsed["sequence_number"] != expected_sequence_number:
                return {
                    "status": "sequence_error",
                    "payload": None,
                    "transport": transport,
                }
            reassembly_buffer.extend(parsed["payload"])
            expected_sequence_number = (expected_sequence_number + 1) & 0x0F
            deadline = time.monotonic() + RESPONSE_TIMEOUT
            if len(reassembly_buffer) >= total_length:
                return {
                    "status": "complete",
                    "payload": bytes(reassembly_buffer[:total_length]),
                    "transport": transport,
                }

    return {
        "status": "timeout",
        "payload": None,
        "transport": transport,
    }


def receive_final_uds_response(expected_service, logger):
    # No new request is sent while NRC 0x78 is active. Each received NRC 0x78
    # starts a fresh response-wait window for the ECU's final response.
    while True:
        result = receive_complete_isotp_payload(logger)
        if result["status"] != "complete":
            return {
                "status": result["status"],
                "payload": None,
                "transport": result.get("transport"),
            }

        payload = result["payload"]
        if not payload:
            continue

        if payload[0] == expected_service + 0x40:
            return {
                "status": "positive",
                "payload": payload,
                "transport": result["transport"],
            }

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1] == expected_service
        ):
            nrc = payload[2]
            if nrc == 0x78:
                print("    [*] NRC 0x78 received. Waiting for final response...")
                continue
            return {
                "status": "negative",
                "payload": payload,
                "nrc": nrc,
                "transport": result["transport"],
            }

        # Ignore unrelated UDS payloads received on the configured RX CAN ID.


# ============================================================
# Diagnostic Session Control (0x10)
# ============================================================
def enter_diagnostic_session(session_id, logger):
    drain_receive_buffer()
    send_uds_request([0x10, session_id], logger)
    response = receive_final_uds_response(0x10, logger)

    if response["status"] == "positive":
        payload = response["payload"]
        if (
            len(payload) >= 2
            and payload[0] == 0x50
            and (payload[1] & 0x7F) == (session_id & 0x7F)
        ):
            time.sleep(SESSION_ENTRY_DELAY)
            return {"entered": True, "nrc": None}

    return {"entered": False, "nrc": response.get("nrc")}


def prepare_testing_session(session_id, logger):
    if session_id is None:
        return {"entered": True, "nrc": None}

    # Start each selected non-default session from Default Session.
    if session_id != 0x01:
        print("[*] Requesting Default Session...")
        default_result = enter_diagnostic_session(0x01, logger)
        if not default_result["entered"]:
            return default_result
        print("[+] Default Session entered.")
        time.sleep(DEFAULT_SESSION_DELAY)

    print(f"[*] Requesting testing Session 0x{session_id:02X}...")
    result = enter_diagnostic_session(session_id, logger)
    if result["entered"]:
        print(f"[+] Testing Session 0x{session_id:02X} entered.")
    return result


# ============================================================
# CommunicationControl (0x28) request and classification
# ============================================================
def test_communication_control_subfunction(subfunction, logger):
    drain_receive_buffer()

    # UDS request: 28 <controlType/subfunction> 01
    # Communication type 0x01 = normal communication messages.
    send_uds_request([SERVICE_ID, subfunction, COMMUNICATION_TYPE], logger)
    response = receive_final_uds_response(SERVICE_ID, logger)

    if response["status"] == "positive":
        payload = response["payload"]

        # Standard matching response is 68 <controlType>. Mask bit 7 so that
        # a response is still matched if the request's suppress-positive-
        # response bit was involved in an OEM implementation.
        matched = (
            len(payload) >= 2
            and payload[0] == POSITIVE_RESPONSE_ID
            and (payload[1] & 0x7F) == (subfunction & 0x7F)
        )
        return {
            "supported": matched,
            "classification": (
                "Positive Response" if matched else "Positive Response Subfunction Mismatch"
            ),
            "nrc": None,
            "transport": response.get("transport"),
        }

    if response["status"] == "negative":
        nrc = response["nrc"]
        supported = nrc in SUPPORTED_NRC_CODES
        return {
            "supported": supported,
            "classification": "Recognised By NRC" if supported else "Negative Response",
            "nrc": nrc,
            "transport": response.get("transport"),
        }

    return {
        "supported": False,
        "classification": response["status"],
        "nrc": None,
        "transport": response.get("transport"),
    }


# ============================================================
# Statistics and scan
# ============================================================
def create_empty_statistics():
    return {
        "processed": 0,
        "supported": 0,
        "unsupported": 0,
        "no_response": 0,
        "nrc_10": 0,
        "nrc_11": 0,
        "nrc_12": 0,
        "nrc_13": 0,
        "nrc_21": 0,
        "nrc_22": 0,
        "nrc_24": 0,
        "nrc_25": 0,
        "nrc_26": 0,
        "nrc_31": 0,
        "nrc_33": 0,
        "nrc_7e": 0,
        "nrc_7f": 0,
        "other_nrc": 0,
        "transport_error": 0,
    }


def count_nrc(statistics, nrc):
    mapping = {
        0x10: "nrc_10",
        0x11: "nrc_11",
        0x12: "nrc_12",
        0x13: "nrc_13",
        0x21: "nrc_21",
        0x22: "nrc_22",
        0x24: "nrc_24",
        0x25: "nrc_25",
        0x26: "nrc_26",
        0x31: "nrc_31",
        0x33: "nrc_33",
        0x7E: "nrc_7e",
        0x7F: "nrc_7f",
    }
    if nrc in mapping:
        statistics[mapping[nrc]] += 1
    elif nrc is not None:
        statistics["other_nrc"] += 1


def scan_communication_control_subfunctions(logger):
    found = []
    statistics = create_empty_statistics()
    total_requests = SUBFUNCTION_SCAN_END - SUBFUNCTION_SCAN_START + 1

    print(
        f"\nScanning CommunicationControl subfunctions "
        f"0x{SUBFUNCTION_SCAN_START:02X} to 0x{SUBFUNCTION_SCAN_END:02X} "
        f"with communicationType 0x{COMMUNICATION_TYPE:02X}..."
    )

    for subfunction in range(SUBFUNCTION_SCAN_START, SUBFUNCTION_SCAN_END + 1):
        result = test_communication_control_subfunction(subfunction, logger)
        statistics["processed"] += 1

        nrc = result.get("nrc")
        count_nrc(statistics, nrc)

        if result["supported"]:
            statistics["supported"] += 1
            found.append(
                {
                    "subfunction": subfunction,
                    "classification": result["classification"],
                    "nrc": nrc,
                    "transport": result.get("transport"),
                }
            )
            detail = result["classification"]
            if nrc is not None:
                detail += f" 0x{nrc:02X} ({NRC_NAMES.get(nrc, 'Unknown NRC')})"
            if result.get("transport"):
                detail += f" | {result['transport']}"
            print(f"\n[+] Supported subfunction: 0x{subfunction:02X} | {detail}")
        else:
            statistics["unsupported"] += 1
            if nrc is None:
                if result["classification"] == "timeout":
                    statistics["no_response"] += 1
                else:
                    statistics["transport_error"] += 1

        percentage = statistics["processed"] * 100.0 / total_requests
        print(
            f"\rProcessed: {statistics['processed']:3}/{total_requests} "
            f"({percentage:6.2f}%) | Subfunction: 0x{subfunction:02X} | "
            f"Supported: {statistics['supported']}",
            end="",
            flush=True,
        )

        # The next request is sent only after the previous request has reached
        # a positive response, final negative response, transport error, or timeout.
        if subfunction < SUBFUNCTION_SCAN_END:
            time.sleep(REQUEST_INTERVAL)

    print()
    return {"supported_subfunctions": found, "statistics": statistics}


# ============================================================
# Console output
# ============================================================
def display_subfunction_grid(supported_subfunctions, columns=10):
    values = [item["subfunction"] for item in supported_subfunctions]
    print("\nEnumerated Communication Control Subfunctions:\n")

    if not values:
        print("No supported Communication Control subfunctions were discovered.")
        return

    cell_width = 7
    horizontal_line = "+" + "+".join("-" * cell_width for _ in range(columns)) + "+"
    for start in range(0, len(values), columns):
        row = values[start:start + columns]
        print(horizontal_line)
        cells = [f"{value:02X}".center(cell_width) for value in row]
        cells.extend([" " * cell_width] * (columns - len(cells)))
        print("|" + "|".join(cells) + "|")
    print(horizontal_line)


def display_results(session_id, result):
    statistics = result["statistics"]
    if session_id is None:
        session_text = "Current Active Session"
    else:
        session_text = (
            f"Session 0x{session_id:02X} "
            f"({SESSION_NAMES.get(session_id, 'OEM Session')})"
        )

    separator = "=" * 100
    print("\n" + separator)
    print("COMMUNICATION CONTROL (0x28) ENUMERATION SUMMARY".center(100))
    print(session_text.center(100))
    print(separator)
    print(f"Request format                      : 28 XX {COMMUNICATION_TYPE:02X}")
    print(f"Total Subfunction Requests Processed: {statistics['processed']}")
    print(f"Total Unsupported Subfunctions      : {statistics['unsupported']}")
    print(f"Total Supported Subfunctions        : {statistics['supported']}")
    print(f"Total No Responses                  : {statistics['no_response']}")

    nrc_rows = [
        (0x10, "nrc_10"), (0x11, "nrc_11"), (0x12, "nrc_12"),
        (0x13, "nrc_13"), (0x21, "nrc_21"), (0x22, "nrc_22"),
        (0x24, "nrc_24"), (0x25, "nrc_25"), (0x26, "nrc_26"),
        (0x31, "nrc_31"), (0x33, "nrc_33"), (0x7E, "nrc_7e"),
        (0x7F, "nrc_7f"),
    ]
    for code, key in nrc_rows:
        print(f"Total NRC 0x{code:02X} Responses             : {statistics[key]}")

    print(f"Total Other NRC Responses           : {statistics['other_nrc']}")
    print(f"Total ISO-TP/Transport Errors       : {statistics['transport_error']}")
    print(separator)
    display_subfunction_grid(result["supported_subfunctions"], columns=10)


def get_log_name(session_id):
    if session_id is None:
        return "Communication_Control_Current_Active_Session"
    name = SESSION_NAMES.get(session_id, "OEM_Session").replace(" ", "_")
    return f"Communication_Control_Session_{session_id:02X}_{name}"


def create_empty_result():
    return {
        "supported_subfunctions": [],
        "statistics": create_empty_statistics(),
    }


# ============================================================
# Per-session execution
# ============================================================
def scan_selected_session(session_id):
    logger = ASCLogger()
    log_started = False
    session_ready = False
    result = create_empty_result()
    log_name = get_log_name(session_id)

    print("\n" + "=" * 100)
    if session_id is None:
        print("Selected Session: NONE, using the ECU's current active session")
    else:
        print(
            f"Selected Session: 0x{session_id:02X} "
            f"({SESSION_NAMES.get(session_id, 'OEM Session')})"
        )
    print(f"ASC Log Name: {log_name}")
    print("=" * 100)

    try:
        # A separate ASC file is created for every selected session.
        logger.start_log(log_name, filters=[TX_ID, RX_ID])
        log_started = True

        if session_id is None:
            session_ready = True
            print("[*] No Diagnostic Session Control request will be sent.")
        else:
            session_result = prepare_testing_session(session_id, logger)
            session_ready = session_result["entered"]
            if not session_ready:
                nrc = session_result.get("nrc")
                if nrc is not None:
                    print(
                        f"[!] Unable to enter Session 0x{session_id:02X}: "
                        f"NRC 0x{nrc:02X} ({NRC_NAMES.get(nrc, 'Unknown NRC')})"
                    )
                else:
                    print(f"[!] Session 0x{session_id:02X} was not confirmed.")

        if session_ready:
            result = scan_communication_control_subfunctions(logger)
            display_results(session_id, result)
        else:
            print("[!] CommunicationControl enumeration skipped for this session.")

    finally:
        # NONE mode intentionally leaves the ECU's active session unchanged.
        if session_id is not None and session_ready and bus is not None and log_started:
            try:
                print("[*] Returning ECU to Default Session...")
                default_result = enter_diagnostic_session(0x01, logger)
                if default_result["entered"]:
                    print("[+] ECU returned to Default Session.")
                else:
                    print("[!] Default Session return was not confirmed.")
            except Exception as error:
                print(f"[!] Default Session cleanup error: {error}")

        if log_started:
            try:
                logger.stop_log()
                print(f"[+] ASC log closed: {log_name}")
            except Exception as error:
                print(f"[!] ASC log close error: {error}")

    return result


# ============================================================
# Main programme
# ============================================================
def main():
    global bus
    global TX_ID
    global RX_ID
    global RESPONSE_TIMEOUT
    global REQUEST_INTERVAL
    global TRANSMIT_CAN_FD

    print("\n" + "=" * 70)
    print("UDS Communication Control Enumeration Tool".center(70))
    print("=" * 70)
    print("[!] Sends requests 28 XX 01 for subfunctions 0x00 through 0x7F.")
    print("[!] CommunicationControl may disable or alter ECU communication.")
    print("[!] Use only on an authorised test bench with a recovery method.")

    TX_ID = get_hex_input("Enter TX CAN ID", 0x471)
    RX_ID = get_hex_input("Enter RX CAN ID", 0x479)
    RESPONSE_TIMEOUT = get_float_input(
        "Enter maximum response timeout for each request",
        DEFAULT_RESPONSE_TIMEOUT,
    )
    REQUEST_INTERVAL = get_float_input(
        "Enter time between two consecutive requests",
        DEFAULT_REQUEST_INTERVAL,
        allow_zero=True,
    )
    TRANSMIT_CAN_FD = get_yes_no_input(
        "Transmit diagnostic requests as CAN FD frames",
        default=False,
    )
    session_selection = get_session_selection()

    print("\nSelected Configuration")
    print("------------------------------------------------------------")
    print(f"TX CAN ID          : 0x{TX_ID:X}")
    print(f"RX CAN ID          : 0x{RX_ID:X}")
    print(f"Transmit mode      : {'CAN FD' if TRANSMIT_CAN_FD else 'Classic CAN'}")
    print(f"Response timeout   : {RESPONSE_TIMEOUT} seconds")
    print(f"Request interval   : {REQUEST_INTERVAL} seconds")
    print(f"Request format     : 28 XX {COMMUNICATION_TYPE:02X}")
    print(f"Subfunction range  : 0x{SUBFUNCTION_SCAN_START:02X} to 0x{SUBFUNCTION_SCAN_END:02X}")
    print(f"Session selection  : {session_selection['mode']}")
    print("------------------------------------------------------------")

    all_results = {}
    try:
        bus = create_can_bus()
        for selected_session in session_selection["sessions"]:
            result = scan_selected_session(selected_session)
            key = "CURRENT" if selected_session is None else f"0x{selected_session:02X}"
            all_results[key] = {
                "session_id": selected_session,
                "result": result,
            }

    except KeyboardInterrupt:
        print("\n[!] CommunicationControl enumeration stopped by user.")
    except can.CanError as error:
        print(f"\n[!] CAN communication error: {error}")
    except Exception as error:
        print(f"\n[!] Unexpected error: {error}")
    finally:
        # Shut down the Vector CAN bus exactly once.
        if bus is not None:
            try:
                print("[*] Shutting down Vector CAN interface...")
                bus.shutdown()
                print("[+] Vector CAN interface shut down.")
            except Exception as error:
                print(f"[!] CAN interface shutdown error: {error}")
            finally:
                bus = None

    print("\n" + "=" * 100)
    print("COMMUNICATION CONTROL ENUMERATION COMPLETED".center(100))
    print("=" * 100)
    for result_data in all_results.values():
        display_results(result_data["session_id"], result_data["result"])


if __name__ == "__main__":
    main()
