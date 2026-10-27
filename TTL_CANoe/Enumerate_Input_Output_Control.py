import time
import can
from ASC_Logger import ASCLogger

# ---------------------------- CAN CONFIGURATION ----------------------------
CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"
CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000
EXTENDED_ID = False

# UDS InputOutputControlByIdentifier
SERVICE_ID = 0x2F
POSITIVE_RESPONSE_ID = 0x6F
DID_SCAN_START = 0xFF00
DID_SCAN_END = 0xFFFF
CONTROL_OPTION_RECORD = 0x00  # returnControlToECU

SESSIONS = {
    0x01: "Default",
    0x02: "Programming",
    0x03: "Extended",
    0x04: "Safety",
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
    0x31: "Request Out Of Range",
    0x33: "Security Access Denied",
    0x78: "Response Pending",
    0x7E: "Sub-function Not Supported In Active Session",
    0x7F: "Service Not Supported In Active Session",
}

# Per requirement, NRC 0x13 and NRC 0x33 indicate a recognised/supported
# InputOutputControlByIdentifier DID during this minimal-request enumeration.
SUPPORTED_NRCS = {0x13, 0x33}

bus = None
TX_ID = None
RX_ID = None
RESPONSE_TIMEOUT = 0.5
REQUEST_INTERVAL = 0.01
TX_FD = False


def hex_input(text, default, maximum=0x1FFFFFFF):
    while True:
        try:
            raw = input(f"{text} (default 0x{default:X}): ").strip()
            value = default if not raw else int(raw, 16)
            if not 0 <= value <= maximum:
                raise ValueError
            return value
        except ValueError:
            print("[!] Invalid hexadecimal value.")


def float_input(text, default, allow_zero=False):
    while True:
        try:
            raw = input(f"{text} (default {default} s): ").strip()
            value = default if not raw else float(raw)
            if value < 0 or (value == 0 and not allow_zero):
                raise ValueError
            return value
        except ValueError:
            print("[!] Invalid time value.")


def yes_no(text, default=False):
    while True:
        raw = input(
            f"{text} (Y/N, default {'Y' if default else 'N'}): "
        ).strip().upper()
        if not raw:
            return default
        if raw in ("Y", "YES"):
            return True
        if raw in ("N", "NO"):
            return False
        print("[!] Enter Y or N.")


def session_input():
    print("\n01 = Default | 02 = Programming | 03 = Extended | 04 = Safety")
    print("ALL = scan every configured session | NONE = use current active session")
    while True:
        raw = input("Select session (01/02/03/04/ALL/NONE): ").strip()
        if raw.upper() == "ALL":
            return "ALL", ALL_SESSIONS.copy()
        if raw.upper() == "NONE":
            return "NONE", [None]
        try:
            value = int(raw, 16)
            if not 0 <= value <= 0x7F:
                raise ValueError
            return "SINGLE", [value]
        except ValueError:
            print("[!] Enter one session value, ALL, or NONE.")


def open_bus():
    return can.Bus(
        interface=CAN_INTERFACE,
        channel=CAN_CHANNEL,
        app_name=CAN_APP_NAME,
        fd=True,
        bitrate=CAN_BITRATE,
        dbitrate=CAN_DATA_BITRATE,
        receive_own_messages=True,
    )


def pad(data, length):
    return list(data) + [0x00] * (length - len(data))


def build_single_frame(payload, use_fd):
    if not use_fd:
        if len(payload) > 7:
            raise ValueError("Classic CAN ISO-TP single-frame payload exceeds 7 bytes")
        return pad([len(payload)] + list(payload), 8)

    if len(payload) <= 7:
        raw = [len(payload)] + list(payload)
    else:
        raw = [0x00, len(payload)] + list(payload)

    for dlc_length in (8, 12, 16, 20, 24, 32, 48, 64):
        if len(raw) <= dlc_length:
            return pad(raw, dlc_length)
    raise ValueError("CAN FD ISO-TP single-frame payload exceeds 64 bytes")


def log_tx(message, logger):
    if not getattr(message, "timestamp", None):
        message.timestamp = time.time()
    logger.log_frame(message, "Tx")


def send_payload(payload, logger, use_fd=None):
    fd = TX_FD if use_fd is None else use_fd
    message = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=EXTENDED_ID,
        is_fd=fd,
        bitrate_switch=fd,
        data=build_single_frame(payload, fd),
    )
    bus.send(message)
    pass


def drain_receive_queue():
    while bus.recv(timeout=0.001) is not None:
        pass


def parse_iso_tp_frame(message):
    data = bytes(message.data)
    if not data:
        return None

    frame_type = data[0] >> 4

    if frame_type == 0x0:  # Single Frame
        payload_length = data[0] & 0x0F
        offset = 1
        if payload_length == 0:  # CAN FD extended SF length
            if len(data) < 2:
                return None
            payload_length = data[1]
            offset = 2
        if payload_length > len(data) - offset:
            return None
        return "SF", data[offset:offset + payload_length]

    if frame_type == 0x1:  # First Frame
        if len(data) < 2:
            return None
        payload_length = ((data[0] & 0x0F) << 8) | data[1]
        offset = 2
        if payload_length == 0:  # ISO-TP extended FF length
            if len(data) < 6:
                return None
            payload_length = int.from_bytes(data[2:6], "big")
            offset = 6
        return "FF", payload_length, data[offset:]

    if frame_type == 0x2:  # Consecutive Frame
        return "CF", data[0] & 0x0F, data[1:]

    return None


def send_flow_control(received_message, logger):
    # CTS, block size 0, STmin 0. Eight bytes works for both classic CAN and CAN FD.
    flow_control = can.Message(
        arbitration_id=TX_ID,
        is_extended_id=EXTENDED_ID,
        is_fd=received_message.is_fd,
        bitrate_switch=(received_message.bitrate_switch
                        if received_message.is_fd else False),
        data=pad([0x30, 0x00, 0x00], 8),
    )
    bus.send(flow_control)
    pass


def receive_payload(logger):
    deadline = time.monotonic() + RESPONSE_TIMEOUT
    payload_buffer = bytearray()
    total_length = None
    expected_sequence = 1
    transport = None

    while time.monotonic() < deadline:
        remaining = max(0.0, deadline - time.monotonic())
        message = bus.recv(timeout=min(0.01, remaining))
        if message is None:
            continue

        logger.log_frame(message, "Rx")
        if message.arbitration_id != RX_ID:
            continue

        frame = parse_iso_tp_frame(message)
        if frame is None:
            continue

        if frame[0] == "SF":
            return {
                "status": "complete",
                "payload": frame[1],
                "transport": "CAN FD SF" if message.is_fd else "CAN SF",
            }

        if frame[0] == "FF":
            total_length = frame[1]
            payload_buffer = bytearray(frame[2])
            expected_sequence = 1
            transport = "CAN FD ISO-TP" if message.is_fd else "CAN ISO-TP"
            send_flow_control(message, logger)
            deadline = time.monotonic() + RESPONSE_TIMEOUT

        elif frame[0] == "CF" and total_length is not None:
            if frame[1] != expected_sequence:
                return {
                    "status": "sequence_error",
                    "payload": None,
                    "transport": transport,
                }
            payload_buffer.extend(frame[2])
            expected_sequence = (expected_sequence + 1) & 0x0F
            deadline = time.monotonic() + RESPONSE_TIMEOUT

        if total_length is not None and len(payload_buffer) >= total_length:
            return {
                "status": "complete",
                "payload": bytes(payload_buffer[:total_length]),
                "transport": transport,
            }

    return {"status": "timeout", "payload": None, "transport": transport}


def receive_final_response(request_sid, logger):
    # Do not send the next request after NRC 0x78. Keep receiving until the ECU
    # supplies the final positive/negative response or a response timeout occurs.
    while True:
        result = receive_payload(logger)
        if result["status"] != "complete":
            return result

        payload = result["payload"]
        if payload and payload[0] == request_sid + 0x40:
            return {
                "status": "positive",
                "payload": payload,
                "transport": result["transport"],
            }

        if (len(payload) >= 3 and payload[0] == 0x7F
                and payload[1] == request_sid):
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

        # Ignore unrelated UDS payloads and continue within a new response window.


def enter_session(session, logger):
    drain_receive_queue()
    send_payload([0x10, session], logger)
    response = receive_final_response(0x10, logger)
    entered = (
        response.get("status") == "positive"
        and len(response.get("payload", b"")) >= 2
        and (response["payload"][1] & 0x7F) == session
    )
    if entered:
        time.sleep(0.5)
    return {"entered": entered, "nrc": response.get("nrc")}


def prepare_session(session, logger):
    if session is None:
        return {"entered": True, "nrc": None}

    # Return to Default before entering another requested session.
    if session != 0x01:
        result = enter_session(0x01, logger)
        if not result["entered"]:
            return result
        time.sleep(0.5)

    return enter_session(session, logger)


def test_did(did, logger):
    drain_receive_queue()

    did_high = (did >> 8) & 0xFF
    did_low = did & 0xFF
    # Minimal IOCBI probe: 2F DID_H DID_L 00 (returnControlToECU).
    # A DID may require a different control option or additional control-state data.
    send_payload([SERVICE_ID, did_high, did_low, CONTROL_OPTION_RECORD], logger)
    response = receive_final_response(SERVICE_ID, logger)

    if response.get("status") == "positive":
        payload = response["payload"]
        matched = (
            len(payload) >= 3
            and payload[0] == POSITIVE_RESPONSE_ID
            and payload[1] == did_high
            and payload[2] == did_low
        )
        return {
            "supported": matched,
            "nrc": None,
            "kind": "Positive" if matched else "Positive response mismatch",
            "transport": response.get("transport"),
        }

    if response.get("status") == "negative":
        nrc = response["nrc"]
        recognised = nrc in SUPPORTED_NRCS
        return {
            "supported": recognised,
            "nrc": nrc,
            "kind": "Recognised NRC" if recognised else "Negative",
            "transport": response.get("transport"),
        }

    return {
        "supported": False,
        "nrc": None,
        "kind": response.get("status", "transport_error"),
        "transport": response.get("transport"),
    }


def empty_stats():
    return {
        "processed": 0,
        "supported": 0,
        "unsupported": 0,
        "timeout": 0,
        "nrc_11": 0,
        "nrc_12": 0,
        "nrc_13": 0,
        "nrc_22": 0,
        "nrc_31": 0,
        "nrc_33": 0,
        "nrc_7e": 0,
        "nrc_7f": 0,
        "other_nrc": 0,
        "transport_error": 0,
    }


def count_nrc(stats, nrc):
    key = {
        0x11: "nrc_11",
        0x12: "nrc_12",
        0x13: "nrc_13",
        0x22: "nrc_22",
        0x31: "nrc_31",
        0x33: "nrc_33",
        0x7E: "nrc_7e",
        0x7F: "nrc_7f",
    }.get(nrc)
    if key:
        stats[key] += 1
    elif nrc is not None:
        stats["other_nrc"] += 1


def scan_dids(logger):
    found = []
    stats = empty_stats()
    total = DID_SCAN_END - DID_SCAN_START + 1

    print(f"\nScanning IOCBI DIDs from 0x{DID_SCAN_START:04X} to 0x{DID_SCAN_END:04X}...")
    for did in range(DID_SCAN_START, DID_SCAN_END + 1):
        result = test_did(did, logger)
        stats["processed"] += 1
        count_nrc(stats, result.get("nrc"))

        if result["supported"]:
            stats["supported"] += 1
            found.append({
                "did": did,
                "nrc": result.get("nrc"),
                "kind": result["kind"],
                "transport": result.get("transport"),
            })
            detail = result["kind"]
            if result.get("nrc") is not None:
                nrc = result["nrc"]
                detail += f" 0x{nrc:02X} ({NRC_NAMES.get(nrc, 'Unknown NRC')})"
            if result.get("transport"):
                detail += f" | {result['transport']}"
            print(f"\n[+] Supported IOCBI DID 0x{did:04X} | {detail}")
        else:
            stats["unsupported"] += 1
            if result.get("nrc") is None:
                if result["kind"] == "timeout":
                    stats["timeout"] += 1
                else:
                    stats["transport_error"] += 1

        print(
            f"\rProcessed {stats['processed']:3}/{total} | "
            f"Current DID 0x{did:04X} | Supported {stats['supported']}",
            end="",
            flush=True,
        )

        # This delay occurs only after the ECU's final response or timeout.
        if did < DID_SCAN_END:
            time.sleep(REQUEST_INTERVAL)

    print()
    return {"found": found, "stats": stats}


def show_summary(session, result):
    stats = result["stats"]
    title = (
        "Current Active Session"
        if session is None
        else f"Session 0x{session:02X} ({SESSIONS.get(session, 'OEM')})"
    )
    line = "=" * 90

    print("\n" + line)
    print("INPUT OUTPUT CONTROL (0x2F) DID ENUMERATION SUMMARY".center(90))
    print(title.center(90))
    print(line)
    print(f"Total DID Requests Processed         : {stats['processed']}")
    print(f"Total Unsupported DIDs               : {stats['unsupported']}")
    print(f"Total Supported DIDs                 : {stats['supported']}")
    print(f"Total No Responses                   : {stats['timeout']}")

    for code, key in (
        (0x11, "nrc_11"), (0x12, "nrc_12"), (0x13, "nrc_13"),
        (0x22, "nrc_22"), (0x31, "nrc_31"), (0x33, "nrc_33"),
        (0x7E, "nrc_7e"), (0x7F, "nrc_7f"),
    ):
        print(f"Total NRC 0x{code:02X} Responses              : {stats[key]}")

    print(f"Total Other NRC Responses          : {stats['other_nrc']}")
    print(f"Total Transport Errors             : {stats['transport_error']}")
    print(line)
    print("Enumerated Input Output Control DIDs:")

    values = [item["did"] for item in result["found"]]
    columns = 10
    cell_width = 8
    border = "+" + "+".join("-" * cell_width for _ in range(columns)) + "+"

    if not values:
        print("None")
        return

    for index in range(0, len(values), columns):
        row = values[index:index + columns]
        print(border)
        cells = [f"{value:04X}".center(cell_width) for value in row]
        cells += [" " * cell_width] * (columns - len(row))
        print("|" + "|".join(cells) + "|")
    print(border)


def log_name(session):
    if session is None:
        return "Input_Output_Control_Current"
    session_name = SESSIONS.get(session, "OEM").replace(" ", "_")
    return f"Input_Output_Control_Session_{session:02X}_{session_name}"


def scan_session(session):
    logger = ASCLogger()
    logger_started = False
    session_ready = None
    result = {"found": [], "stats": empty_stats()}

    try:
        logger.start_log(log_name(session), filters=[TX_ID, RX_ID])
        logger_started = True

        session_ready = prepare_session(session, logger)
        if not session_ready["entered"]:
            nrc = session_ready.get("nrc")
            nrc_text = "No response" if nrc is None else f"0x{nrc:02X} ({NRC_NAMES.get(nrc, 'Unknown NRC')})"
            print(f"[!] Session entry failed: {nrc_text}")
            show_summary(session, result)
            return result

        result = scan_dids(logger)
        show_summary(session, result)
        return result

    finally:
        if logger_started:
            if (session is not None and session_ready
                    and session_ready.get("entered") and bus is not None):
                try:
                    enter_session(0x01, logger)
                except Exception as error:
                    print(f"[!] Default-session cleanup failed: {error}")
            logger.stop_log()
            print(f"[+] ASC log closed: {log_name(session)}")


def main():
    global bus, TX_ID, RX_ID, RESPONSE_TIMEOUT, REQUEST_INTERVAL, TX_FD

    print("\n" + "=" * 70)
    print("Input Output Control DID Enumeration Tool".center(70))
    print("=" * 70)
    print("[!] Use only on an authorised ECU/test bench.")
    print("[*] Probe format: 2F <DID_H> <DID_L> 00 (returnControlToECU).")
    print("[*] NRC 0x13 and 0x33 are counted as supported DIDs.")

    TX_ID = hex_input("Enter TX CAN ID", 0x471)
    RX_ID = hex_input("Enter RX CAN ID", 0x479)
    RESPONSE_TIMEOUT = float_input("Enter maximum response timeout for each DID", 0.5)
    REQUEST_INTERVAL = float_input(
        "Enter time between consecutive DID requests", 0.01, allow_zero=True
    )
    TX_FD = yes_no("Transmit diagnostic requests as CAN FD", False)
    _, sessions = session_input()

    all_results = {}

    try:
        bus = open_bus()
        print("[+] Vector CAN interface opened.")

        for session in sessions:
            key = "CURRENT" if session is None else f"0x{session:02X}"
            all_results[key] = {
                "session": session,
                "result": scan_session(session),
            }

    except KeyboardInterrupt:
        print("\n[!] Enumeration stopped by user.")
    except can.CanError as error:
        print(f"\n[!] CAN error: {error}")
    except Exception as error:
        print(f"\n[!] Unexpected error: {error}")
    finally:
        if bus is not None:
            try:
                bus.shutdown()
                print("[+] Vector CAN interface shut down.")
            except Exception as error:
                print(f"[!] Bus shutdown error: {error}")
            bus = None

    print("\n" + "=" * 90)
    print("INPUT OUTPUT CONTROL DID ENUMERATION COMPLETED".center(90))
    print("=" * 90)
    for item in all_results.values():
        show_summary(item["session"], item["result"])


if __name__ == "__main__":
    main()
