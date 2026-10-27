import time
import can
from ASC_Logger import ASCLogger

# ======================== CAN configuration ========================
CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"
CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000
USE_EXTENDED_CAN_ID = False

# ======================== Enumeration configuration ===============
RID_SCAN_START = 0xFE00
RID_SCAN_END = 0xFFFF
ROUTINE_CONTROL_TYPE = 0x01  # StartRoutine, as requested
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
    0x10: "General Reject", 0x11: "Service Not Supported",
    0x12: "Sub-function Not Supported", 0x13: "Incorrect Message Length Or Invalid Format",
    0x14: "Response Too Long", 0x21: "Busy Repeat Request",
    0x22: "Conditions Not Correct", 0x24: "Request Sequence Error",
    0x25: "No Response From Subnet Component", 0x26: "Failure Prevents Execution",
    0x31: "Request Out Of Range", 0x33: "Security Access Denied",
    0x35: "Invalid Key", 0x36: "Exceeded Number Of Attempts",
    0x37: "Required Time Delay Not Expired", 0x70: "Upload/Download Not Accepted",
    0x71: "Transfer Data Suspended", 0x72: "General Programming Failure",
    0x73: "Wrong Block Sequence Counter", 0x78: "Response Pending",
    0x7E: "Sub-function Not Supported In Active Session",
    0x7F: "Service Not Supported In Active Session",
}

bus = None
TX_ID = None
RX_ID = None
RESPONSE_TIMEOUT = None
REQUEST_INTERVAL = None
TRANSMIT_CAN_FD = False


def get_hex_input(prompt, default, minimum=0, maximum=0x1FFFFFFF):
    while True:
        value = input(f"{prompt} (default 0x{default:X}): ").strip()
        try:
            result = default if value == "" else int(value, 16)
            if not minimum <= result <= maximum:
                raise ValueError
            return result
        except ValueError:
            print(f"[!] Enter a hexadecimal value from 0x{minimum:X} to 0x{maximum:X}.")


def get_float_input(prompt, default, allow_zero=False):
    while True:
        value = input(f"{prompt} (default {default} seconds): ").strip()
        try:
            result = default if value == "" else float(value)
            if result < 0 or (result == 0 and not allow_zero):
                raise ValueError
            return result
        except ValueError:
            print("[!] Enter a valid non-negative number." if allow_zero else "[!] Enter a number greater than zero.")


def get_yes_no(prompt, default=False):
    default_text = "Y" if default else "N"
    while True:
        value = input(f"{prompt} (Y/N, default {default_text}): ").strip().upper()
        if value == "": return default
        if value in ("Y", "YES"): return True
        if value in ("N", "NO"): return False
        print("[!] Enter Y or N.")


def get_session_selection():
    print("\nDiagnostic Session Selection")
    print("  01 Default | 02 Programming | 03 Extended | 04 Safety")
    print("  ALL = all configured sessions | NONE = current active session")
    while True:
        value = input("Select session: ").strip()
        if value.upper() == "ALL": return {"mode": "ALL", "sessions": ALL_SESSIONS.copy()}
        if value.upper() == "NONE": return {"mode": "NONE", "sessions": [None]}
        try:
            session = int(value, 16)
            if not 0 <= session <= 0x7F: raise ValueError
            return {"mode": "SINGLE", "sessions": [session]}
        except ValueError:
            print("[!] Enter one session ID, ALL, or NONE.")


def create_can_bus():
    print("[*] Opening Vector CAN interface...")
    result = can.Bus(interface=CAN_INTERFACE, channel=CAN_CHANNEL,
                     app_name=CAN_APP_NAME, fd=True, bitrate=CAN_BITRATE,
                     dbitrate=CAN_DATA_BITRATE, receive_own_messages=True)
    print("[+] Vector CAN interface opened.")
    return result


def valid_fd_length(required):
    for length in (8, 12, 16, 20, 24, 32, 48, 64):
        if required <= length: return length
    raise ValueError("CAN FD frame exceeds 64 bytes.")


def pad(data, length):
    return list(data) + [0x00] * (length - len(data))


def make_single_frame(payload):
    if not payload: raise ValueError("Empty UDS payload.")
    if not TRANSMIT_CAN_FD:
        if len(payload) > 7: raise ValueError("Classic CAN single-frame payload exceeds 7 bytes.")
        return pad([len(payload)] + list(payload), 8)
    if len(payload) <= 7:
        raw = [len(payload)] + list(payload)
    else:
        if len(payload) > 62: raise ValueError("CAN FD single-frame payload exceeds 62 bytes.")
        raw = [0x00, len(payload)] + list(payload)
    return pad(raw, valid_fd_length(max(8, len(raw))))


def log_tx(message, logger):
    if not getattr(message, "timestamp", None): message.timestamp = time.time()
    logger.log_frame(message, "Tx")


def send_uds(payload, logger):
    message = can.Message(arbitration_id=TX_ID, is_extended_id=USE_EXTENDED_CAN_ID,
                          is_fd=TRANSMIT_CAN_FD, bitrate_switch=TRANSMIT_CAN_FD,
                          data=make_single_frame(payload))
    bus.send(message)
    pass


def drain_rx():
    while bus is not None and bus.recv(timeout=0.001) is not None:
        pass


def send_flow_control(first_frame, logger):
    data = pad([0x30, FLOW_CONTROL_BLOCK_SIZE, FLOW_CONTROL_ST_MIN], 8)
    frame = can.Message(arbitration_id=TX_ID, is_extended_id=USE_EXTENDED_CAN_ID,
                        is_fd=first_frame.is_fd,
                        bitrate_switch=first_frame.bitrate_switch if first_frame.is_fd else False,
                        data=data)
    bus.send(frame)
    pass


def parse_isotp(message):
    data = bytes(message.data)
    if not data: return None
    kind = data[0] >> 4
    if kind == 0:
        length = data[0] & 0x0F
        offset = 1
        if length == 0:
            if len(data) < 2 or data[1] == 0: return None
            length, offset = data[1], 2
        if length > len(data) - offset: return None
        return {"type": "single", "payload": data[offset:offset + length]}
    if kind == 1:
        if len(data) < 2: return None
        length = ((data[0] & 0x0F) << 8) | data[1]
        offset = 2
        if length == 0:
            if len(data) < 6: return None
            length, offset = int.from_bytes(data[2:6], "big"), 6
        return {"type": "first", "length": length, "payload": data[offset:]}
    if kind == 2:
        return {"type": "consecutive", "sn": data[0] & 0x0F, "payload": data[1:]}
    return {"type": "other"}


def receive_isotp(logger):
    deadline = time.monotonic() + RESPONSE_TIMEOUT
    buffer = bytearray()
    total = None
    expected_sn = 1
    transport = None
    while time.monotonic() < deadline:
        message = bus.recv(timeout=min(0.01, max(0, deadline - time.monotonic())))
        if message is None: continue
        logger.log_frame(message, "Rx")
        if message.arbitration_id != RX_ID: continue
        parsed = parse_isotp(message)
        if not parsed: continue
        if parsed["type"] == "single":
            return {"status": "complete", "payload": parsed["payload"],
                    "transport": "CAN FD ISO-TP SF" if message.is_fd else "CAN ISO-TP SF"}
        if parsed["type"] == "first":
            total = parsed["length"]
            buffer = bytearray(parsed["payload"])
            expected_sn = 1
            transport = "CAN FD ISO-TP MF" if message.is_fd else "CAN ISO-TP MF"
            send_flow_control(message, logger)
            deadline = time.monotonic() + RESPONSE_TIMEOUT
            if len(buffer) >= total:
                return {"status": "complete", "payload": bytes(buffer[:total]), "transport": transport}
        elif parsed["type"] == "consecutive" and total is not None:
            if parsed["sn"] != expected_sn:
                return {"status": "sequence_error", "payload": None, "transport": transport}
            buffer.extend(parsed["payload"])
            expected_sn = (expected_sn + 1) & 0x0F
            deadline = time.monotonic() + RESPONSE_TIMEOUT
            if len(buffer) >= total:
                return {"status": "complete", "payload": bytes(buffer[:total]), "transport": transport}
    return {"status": "timeout", "payload": None, "transport": transport}


def receive_final_uds(expected_sid, logger):
    pending = False
    while True:
        result = receive_isotp(logger)
        if result["status"] != "complete":
            return {"status": result["status"], "payload": None, "transport": result.get("transport")}
        payload = result["payload"]
        if not payload: continue
        if payload[0] == expected_sid + 0x40:
            return {"status": "positive", "payload": payload, "transport": result["transport"]}
        if len(payload) >= 3 and payload[0] == 0x7F and payload[1] == expected_sid:
            if payload[2] == 0x78:
                pending = True
                print("    [*] NRC 0x78 received; waiting for final response...")
                continue
            return {"status": "negative", "payload": payload, "nrc": payload[2],
                    "transport": result["transport"], "pending_seen": pending}


def enter_session(session, logger):
    drain_rx()
    send_uds([0x10, session], logger)
    result = receive_final_uds(0x10, logger)
    if result["status"] == "positive" and len(result["payload"]) >= 2 and (result["payload"][1] & 0x7F) == session:
        time.sleep(SESSION_ENTRY_DELAY)
        return {"entered": True, "nrc": None}
    return {"entered": False, "nrc": result.get("nrc")}


def prepare_session(session, logger):
    if session is None: return {"entered": True, "nrc": None}
    if session != 0x01:
        result = enter_session(0x01, logger)
        if not result["entered"]: return result
        time.sleep(DEFAULT_SESSION_DELAY)
    return enter_session(session, logger)


def request_rid(rid, logger):
    drain_rx()
    send_uds([0x31, ROUTINE_CONTROL_TYPE, (rid >> 8) & 0xFF, rid & 0xFF], logger)
    result = receive_final_uds(0x31, logger)
    if result["status"] == "positive":
        p = result["payload"]
        if len(p) >= 4 and (p[1] & 0x7F) == ROUTINE_CONTROL_TYPE and p[2] == ((rid >> 8) & 0xFF) and p[3] == (rid & 0xFF):
            return {"supported": True, "classification": "positive", "nrc": None,
                    "data_length": len(p) - 4, "transport": result["transport"]}
        return {"supported": False, "classification": "RID mismatch", "nrc": None}
    if result["status"] == "negative":
        # NRC 0x13 and NRC 0x33 are treated as evidence that the RID
        # was recognised by the ECU, as requested.
        # NRC 0x31 remains classified as an unsupported RID.
        supported = result["nrc"] in (0x13, 0x33)
        return {"supported": supported, "classification": "recognised NRC" if supported else "negative",
                "nrc": result["nrc"], "transport": result["transport"]}
    return {"supported": False, "classification": result["status"], "nrc": None}


def empty_stats():
    return {"processed": 0, "supported": 0, "unsupported": 0, "no_response": 0,
            "nrc_13": 0, "nrc_22": 0, "nrc_24": 0, "nrc_31": 0,
            "nrc_33": 0, "nrc_7e": 0, "nrc_7f": 0, "other_nrc": 0,
            "transport_error": 0}


def scan_rids(logger):
    found, stats = [], empty_stats()
    total = RID_SCAN_END - RID_SCAN_START + 1
    for rid in range(RID_SCAN_START, RID_SCAN_END + 1):
        result = request_rid(rid, logger)

        #

        # Count NRC responses regardless of whether

        # the RID is classified as supported or not.

        #

        nrc = result.get("nrc")

        if nrc == 0x13:

            stats["nrc_13"] += 1


        elif nrc == 0x22:

            stats["nrc_22"] += 1


        elif nrc == 0x24:

            stats["nrc_24"] += 1


        elif nrc == 0x31:

            stats["nrc_31"] += 1


        elif nrc == 0x33:

            stats["nrc_33"] += 1


        elif nrc == 0x7E:

            stats["nrc_7e"] += 1


        elif nrc == 0x7F:

            stats["nrc_7f"] += 1


        elif nrc is not None:

            stats["other_nrc"] += 1

        stats["processed"] += 1
        if result["supported"]:
            stats["supported"] += 1
            found.append({"rid": rid, "nrc": result.get("nrc"),
                          "transport": result.get("transport"), "data_length": result.get("data_length", 0)})
            print(f"\n[+] Discovered RID 0x{rid:04X} | {result['classification']}")
        else:
            stats["unsupported"] += 1
            if result["classification"] == "timeout": stats["no_response"] += 1
            else: stats["transport_error"] += 1
        pct = stats["processed"] * 100.0 / total
        print(f"\rProcessed {stats['processed']:5}/{total} ({pct:6.2f}%) | RID 0x{rid:04X} | Found {stats['supported']}", end="", flush=True)
        if rid < RID_SCAN_END: time.sleep(REQUEST_INTERVAL)
    print()
    return {"rids": found, "statistics": stats}


def display_grid(rids, columns=10):
    values = [x["rid"] for x in rids]
    if not values:
        print("No matching positive responses or configured recognised NRC results.")
        return
    width = 8
    line = "+" + "+".join("-" * width for _ in range(columns)) + "+"
    for start in range(0, len(values), columns):
        row = values[start:start + columns]
        print(line)
        cells = [f"{value:04X}".center(width) for value in row]
        cells += [" " * width] * (columns - len(cells))
        print("|" + "|".join(cells) + "|")
    print(line)


def display_results(session, result):
    stats = result["statistics"]
    title = "Current Active Session" if session is None else f"Session 0x{session:02X} ({SESSION_NAMES.get(session, 'OEM Session')})"
    line = "=" * 100
    print("\n" + line)
    print("ROUTINE CONTROL (0x31) SERVICE ENUMERATION SUMMARY".center(100))
    print(title.center(100))
    print(line)
    print(f"Total Routine Requests Processed : {stats['processed']}")
    print(f"Total Unsupported Routines Found : {stats['unsupported']}")
    print(f"Total Supported Routines Found   : {stats['supported']}")
    print(f"Total No Responses               : {stats['no_response']}")
    print(f"Total NRC 0x13 Responses         : {stats['nrc_13']}")
    print(f"Total NRC 0x22 Responses         : {stats['nrc_22']}")
    print(f"Total NRC 0x24 Responses         : {stats['nrc_24']}")
    print(f"Total NRC 0x31 Responses         : {stats['nrc_31']}")
    print(f"Total NRC 0x33 Responses         : {stats['nrc_33']}")
    print(f"Total Other NRC Responses        : {stats['other_nrc']}")
    print(f"Total ISO-TP/Transport Errors     : {stats['transport_error']}")
    print(line)
    print("Enumerated Routine Identifiers (RID):".center(100))
    display_grid(result["rids"])


def log_name(session):
    if session is None: return "Routine_RID_Enumeration_Current_Active_Session"
    name = SESSION_NAMES.get(session, "OEM_Session").replace(" ", "_")
    return f"Routine_RID_Enumeration_Session_{session:02X}_{name}"


def scan_selected_session(session):
    logger = ASCLogger()
    started = False
    result = {"rids": [], "statistics": empty_stats()}
    try:
        logger.start_log(log_name(session), filters=[TX_ID, RX_ID])
        started = True
        ready = prepare_session(session, logger)
        if not ready["entered"]:
            print(f"[!] Could not enter session; NRC={ready.get('nrc')}")
            return result
        result = scan_rids(logger)
        display_results(session, result)
        return result
    finally:
        if started:
            if session is not None and bus is not None:
                try: enter_session(0x01, logger)
                except Exception as error: print(f"[!] Default-session cleanup failed: {error}")
            logger.stop_log()
            print(f"[+] ASC log closed: {log_name(session)}")


print("\n" + "=" * 64)
print("Routine Identifier Enumeration Tool".center(64))
print("=" * 64)
TX_ID = get_hex_input("Enter TX CAN ID", 0x471)
RX_ID = get_hex_input("Enter RX CAN ID", 0x479)
RESPONSE_TIMEOUT = get_float_input("Enter maximum response timeout for each RID", DEFAULT_RESPONSE_TIMEOUT)
REQUEST_INTERVAL = get_float_input("Enter time between consecutive RID requests", DEFAULT_REQUEST_INTERVAL, allow_zero=True)
TRANSMIT_CAN_FD = get_yes_no("Transmit diagnostic requests as CAN FD", False)
selection = get_session_selection()

print("\nSelected Configuration")
print(f"TX ID: 0x{TX_ID:X} | RX ID: 0x{RX_ID:X}")
print(f"Mode: {'CAN FD' if TRANSMIT_CAN_FD else 'Classic CAN'}")
print(f"RID range: 0x{RID_SCAN_START:04X} to 0x{RID_SCAN_END:04X}")
print(f"RoutineControl type: 0x{ROUTINE_CONTROL_TYPE:02X} (StartRoutine)")
print(f"Sessions: {selection['mode']}")

all_results = {}
try:
    bus = create_can_bus()
    for selected in selection["sessions"]:
        all_results["CURRENT" if selected is None else f"0x{selected:02X}"] = {
            "session": selected, "result": scan_selected_session(selected)
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

print("\n" + "=" * 100)
print("ROUTINE IDENTIFIER ENUMERATION COMPLETED".center(100))
print("=" * 100)
for item in all_results.values():
    display_results(item["session"], item["result"])
