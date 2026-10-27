import can
import time

from ASC_Logger import ASCLogger


# ====================================================
# Fixed CAN Interface Configuration
# ====================================================
#
# The CAN bus is created locally in this script.
# Do not import "bus" from bus_manager.py for this
# script because it can result in reusing a bus that
# has already been shut down.
#
# Update these values if your Vector configuration
# differs.
# ====================================================

CAN_INTERFACE = "vector"
CAN_CHANNEL = 0
CAN_APP_NAME = "Python"

CAN_FD_ENABLED = True
CAN_BITRATE = 500000
CAN_DATA_BITRATE = 2000000

USE_EXTENDED_CAN_ID = False


# ====================================================
# Service Scan Configuration
# ====================================================

SERVICE_SCAN_START = 0x00
SERVICE_SCAN_END = 0xFF

DEFAULT_SESSION_DELAY = 0.50
SESSION_ENTRY_DELAY = 0.50
INTER_REQUEST_DELAY = 0.02


# ====================================================
# Session Configuration
# ====================================================

SESSION_NAMES = {
    0x01: "Default Session",
    0x02: "Programming Session",
    0x03: "Extended Session",
    0x04: "Safety System Session"
}

# Sessions scanned when the user selects ALL.
#
# Add OEM-specific sessions here when required.
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
# UDS Service Names
# ====================================================

UDS_SERVICE_NAMES = {
    0x10: "Diagnostic Session Control",
    0x11: "ECU Reset",
    0x14: "Clear Diagnostic Information",
    0x19: "Read DTC Information",
    0x22: "Read Data By Identifier",
    0x23: "Read Memory By Address",
    0x24: "Read Scaling Data By Identifier",
    0x27: "Security Access",
    0x28: "Communication Control",
    0x29: "Authentication",
    0x2A: "Read Data By Periodic Identifier",
    0x2C: "Dynamically Define Data Identifier",
    0x2E: "Write Data By Identifier",
    0x2F: "Input Output Control By Identifier",
    0x31: "Routine Control",
    0x34: "Request Download",
    0x35: "Request Upload",
    0x36: "Transfer Data",
    0x37: "Request Transfer Exit",
    0x38: "Request File Transfer",
    0x3D: "Write Memory By Address",
    0x3E: "Tester Present",
    0X85: "DTC Control Setting"
}


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
# NRC Classification
# ====================================================
#
# NRC 0x11:
#     The requested service is not supported.
#
# NRC 0x7F:
#     The service is not supported in the currently
#     active diagnostic session.
#
# These responses are excluded from the supported
# service list for that session.
#
# The following NRCs indicate that the requested SID
# was recognised by the ECU. The request may have been
# rejected because the one-byte probe did not contain
# valid parameters or because ECU conditions were not
# correct.
# ====================================================

RECOGNISED_SERVICE_NRCS = {
    0x10,
    0x12,
    0x13,
    0x14,
    0x21,
    0x22,
    0x24,
    0x25,
    0x26,
    0x31,
    0x33,
    0x35,
    0x36,
    0x37,
    0x70,
    0x71,
    0x72,
    0x73,
    0x7E
}

NOT_SUPPORTED_NRCS = {
    0x11,
    0x7F
}


# ====================================================
# Global Runtime Objects
# ====================================================

bus = None


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

            print(
                "[!] Invalid hexadecimal value."
            )

            print(
                "    Examples: 471, 0x471, 7E0"
            )


def get_float_input(prompt, default):

    while True:

        value = input(
            f"{prompt} (default {default}): "
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
                "[!] Enter a value greater than zero."
            )


def get_session_selection():

    print()
    print("==================================================")
    print("Diagnostic Session Selection")
    print("==================================================")
    print()
    print("Enter one diagnostic session:")
    print("  01    Default Session")
    print("  02    Programming Session")
    print("  03    Extended Session")
    print("  04    Safety System Session")
    print()
    print("Other supported input:")
    print("  ALL   Scan all configured diagnostic sessions")
    print("  NONE  Do not change the current ECU session")
    print()
    print("Examples:")
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

            session_id = int(
                value,
                16
            )

            if not 0x00 <= session_id <= 0x7F:

                print(
                    "[!] Session must be between "
                    "0x00 and 0x7F."
                )

                continue

            return {
                "mode": "SINGLE",
                "sessions": [session_id]
            }

        except ValueError:

            print(
                "[!] Invalid selection."
            )

            print(
                "    Enter one session such as 01, "
                "02 or 03, or enter ALL or NONE."
            )


# ====================================================
# CAN Bus Creation
# ====================================================

def create_can_bus():

    print()
    print("[*] Opening Vector CAN interface...")

    can_bus = can.Bus(
        interface=CAN_INTERFACE,
        channel=CAN_CHANNEL,
        app_name=CAN_APP_NAME,
        fd=CAN_FD_ENABLED,
        bitrate=CAN_BITRATE,
        dbitrate=CAN_DATA_BITRATE,
        receive_own_messages=True
    )

    print("[+] Vector CAN interface opened.")

    return can_bus


# ====================================================
# ISO-TP Single-Frame Helpers
# ====================================================

def create_single_frame(payload):

    if len(payload) == 0:

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

    if payload_length > (
        len(message.data) - 1
    ):

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

    # The ASC logger requires a timestamp for the
    # transmitted message. python-can may not assign
    # a timestamp to a locally created Tx object.

    if not getattr(
            message,
            "timestamp",
            None):

        message.timestamp = time.time()

    pass


# ====================================================
# Service Response Handling
# ====================================================

def wait_for_service_response(
        requested_service,
        logger):

    deadline = (
        time.monotonic()
        + REQUEST_TIMEOUT
    )

    pending_received = False

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

        if (
            message.arbitration_id
            != RX_ID
        ):
            continue

        payload = extract_single_frame_payload(
            message
        )

        if payload is None:
            continue

        expected_positive_sid = (
            requested_service + 0x40
        )

        # --------------------------------------------
        # Positive response
        # --------------------------------------------

        if (
            len(payload) >= 1
            and payload[0]
            == expected_positive_sid and payload[0] != 0X7F
        ):

            return {
                "supported": True,
                "classification": "Positive Response",
                "nrc": None,
                "payload": payload
            }

        # --------------------------------------------
        # Negative response
        #
        # 7F <requested SID> <NRC>
        # --------------------------------------------

        if (
            len(payload) >= 3
            and payload[0] == 0x7F
            and payload[1]
            == requested_service
        ):

            nrc = payload[2]

            # NRC 0x78 means the ECU has accepted the
            # request but needs additional processing
            # time. Restart the selected timeout.

            if nrc == 0x78:

                pending_received = True

                deadline = (
                    time.monotonic()
                    + REQUEST_TIMEOUT
                )

                continue

            if nrc in NOT_SUPPORTED_NRCS:

                return {
                    "supported": False,
                    "classification": "Not Supported",
                    "nrc": nrc,
                    "payload": payload
                }

            if nrc in RECOGNISED_SERVICE_NRCS:

                return {
                    "supported": True,
                    "classification": "Recognised By NRC",
                    "nrc": nrc,
                    "payload": payload
                }

            return {
                "supported": False,
                "classification": "Unclassified NRC",
                "nrc": nrc,
                "payload": payload
            }

    if pending_received:

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
        "payload": None
    }


# ====================================================
# Diagnostic Session Response Handling
# ====================================================

def wait_for_session_response(
        requested_session,
        logger):

    deadline = (
        time.monotonic()
        + REQUEST_TIMEOUT
    )

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

        if (
            message.arbitration_id
            != RX_ID
        ):
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
            and payload[1]
            == requested_session
        ):

            return {
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

            if nrc == 0x78:

                deadline = (
                    time.monotonic()
                    + REQUEST_TIMEOUT
                )

                continue

            return {
                "entered": False,
                "nrc": nrc,
                "payload": payload
            }

    return {
        "entered": False,
        "nrc": None,
        "payload": None
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


def return_to_default_session(
        logger):

    result = enter_diagnostic_session(
        0x01,
        logger
    )

    time.sleep(
        DEFAULT_SESSION_DELAY
    )

    return result


# ====================================================
# UDS Service Scanner
# ====================================================

def scan_services(
        session_id,
        logger):

    supported_services = []

    print()
    print(
        f"Scanning service IDs from "
        f"0x{SERVICE_SCAN_START:02X} to "
        f"0x{SERVICE_SCAN_END:02X}..."
    )
    print()

    for service_id in range(
            SERVICE_SCAN_START,
            SERVICE_SCAN_END + 1):

        print(
            f"Checking Service 0x{service_id:02X}",
            end=""
        )

        drain_receive_buffer()

        # Send only the service identifier:
        #
        # 01 <SID> 00 00 00 00 00 00
        #
        # The request intentionally does not contain
        # valid sub-functions, identifiers, addresses,
        # routines or reset types.

        send_uds_request(
            [
                service_id
            ],
            logger
        )

        result = wait_for_service_response(
            service_id,
            logger
        )

        if result["supported"]:

            service_result = {
                "service_id": service_id,
                "classification":
                    result["classification"],
                "nrc": result["nrc"]
            }

            supported_services.append(
                service_result
            )

            if result["nrc"] is None:

                print(
                    "  [+] Positive response"
                )

            else:

                nrc_name = NRC_NAMES.get(
                    result["nrc"],
                    "Unknown NRC"
                )

                print(
                    f"  [+] Recognised by NRC "
                    f"0x{result['nrc']:02X} "
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

        time.sleep(
            INTER_REQUEST_DELAY
        )

    return supported_services


# ====================================================
# Result Table
# ====================================================

def display_service_results(
        session_id,
        services):

    if session_id is None:

        session_text = (
            "Current Active Session "
            "(session change not requested)"
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
        f"Enumerated UDS Services for {session_text}:"
    )
    print()

    print(
        "+------------+----------------------------------------+"
    )
    print(
        "| Service ID | UDS Service Name                       |"
    )
    print(
        "+------------+----------------------------------------+"
    )

    for service in services:

        service_id = service[
            "service_id"
        ]

        service_name = UDS_SERVICE_NAMES.get(
            service_id,
            f"Unknown / OEM Service 0x{service_id:02X}"
        )

        print(
            f"| 0x{service_id:02X}       | "
            f"{service_name:<38} |"
        )

    print(
        "+------------+----------------------------------------+"
    )

    print(
        f"\nTotal recognised services: "
        f"{len(services)}"
    )


# ====================================================
# Log Name
# ====================================================

def get_log_name(
        session_id):

    if session_id is None:

        return (
            "UDS_Service_Enumeration_"
            "Current_Active_Session"
        )

    session_name = SESSION_NAMES.get(
        session_id,
        "OEM_Session"
    )

    safe_session_name = (
        session_name
        .replace(" ", "_")
    )

    return (
        f"UDS_Service_Enumeration_"
        f"Session_{session_id:02X}_"
        f"{safe_session_name}"
    )


# ====================================================
# Scan One Selected Session
# ====================================================

def scan_selected_session(
        session_id):

    logger = ASCLogger()

    log_name = get_log_name(
        session_id
    )

    services = []

    session_ready = False

    print()
    print("=" * 60)

    if session_id is None:

        print(
            "Scanning services in the current "
            "active ECU session"
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
        f"ASC Log: {log_name}"
    )

    print("=" * 60)

    try:

        logger.start_log(
            log_name,
            filters=[
                TX_ID,
                RX_ID
            ]
        )

        # NONE means do not request a diagnostic
        # session change. Scan the ECU in whichever
        # session is currently active.

        if session_id is None:

            session_ready = True

            print(
                "[*] Session selection is NONE."
            )

            print(
                "[*] No Diagnostic Session Control "
                "request will be sent."
            )

        else:

            # Before entering Programming, Extended,
            # Safety or an OEM session, first request
            # Default Session.

            if session_id != 0x01:

                print(
                    "[*] Requesting Default Session "
                    "before entering the selected "
                    "session..."
                )

                default_result = (
                    return_to_default_session(
                        logger
                    )
                )

                if default_result["entered"]:

                    print(
                        "[+] Default Session entered."
                    )

                elif default_result["nrc"] is not None:

                    nrc_name = NRC_NAMES.get(
                        default_result["nrc"],
                        "Unknown NRC"
                    )

                    print(
                        f"[!] Default Session request "
                        f"returned NRC "
                        f"0x{default_result['nrc']:02X} "
                        f"({nrc_name})."
                    )

                else:

                    print(
                        "[!] No response received for "
                        "Default Session request."
                    )

            print(
                f"[*] Requesting Diagnostic Session "
                f"0x{session_id:02X}..."
            )

            session_result = (
                enter_diagnostic_session(
                    session_id,
                    logger
                )
            )

            if session_result["entered"]:

                session_ready = True

                print(
                    f"[+] Diagnostic Session "
                    f"0x{session_id:02X} entered."
                )

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
                    f"[!] No response received while "
                    f"entering Session "
                    f"0x{session_id:02X}."
                )

        if session_ready:

            services = scan_services(
                session_id,
                logger
            )

            display_service_results(
                session_id,
                services
            )

        else:

            print(
                "[!] Service scan skipped because "
                "the selected session was not "
                "confirmed."
            )

    finally:

        # For a selected diagnostic session, request
        # Default Session before closing its log.
        #
        # For NONE, do not change the ECU session.

        if (
            session_ready
            and session_id is not None
            and bus is not None
        ):

            try:

                print()
                print(
                    "[*] Returning ECU to "
                    "Default Session..."
                )

                final_result = (
                    return_to_default_session(
                        logger
                    )
                )

                if final_result["entered"]:

                    print(
                        "[+] ECU returned to "
                        "Default Session."
                    )

                else:

                    print(
                        "[!] Default Session return "
                        "was not confirmed."
                    )

            except can.CanError as error:

                print(
                    f"[!] CAN error while returning "
                    f"to Default Session: {error}"
                )

        try:

            logger.stop_log()

            print(
                f"[+] ASC log stored for "
                f"{get_log_name(session_id)}"
            )

        except Exception as error:

            print(
                f"[!] Error while closing ASC log: "
                f"{error}"
            )

    return services


# ====================================================
# Main Programme
# ====================================================

print()
print("==================================================")
print("          UDS Service Enumeration Tool")
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

REQUEST_TIMEOUT = get_float_input(
    "Enter response timeout for each request in seconds",
    0.20
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
print(f"Request timeout    : {REQUEST_TIMEOUT} seconds")
print(
    f"Service scan range : "
    f"0x{SERVICE_SCAN_START:02X} to "
    f"0x{SERVICE_SCAN_END:02X}"
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
        "Action              : Scan current active session"
    )

else:

    selected_session = SELECTED_SESSIONS[0]

    print(
        f"Session selection   : "
        f"0x{selected_session:02X}"
    )

print("--------------------------------------------------")


# ====================================================
# Execute Scan
# ====================================================

all_results = {}

try:

    bus = create_can_bus()

    print()
    print("[*] Starting UDS service enumeration...")

    for selected_session in SELECTED_SESSIONS:

        result = scan_selected_session(
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
            "services": result
        }

except KeyboardInterrupt:

    print()
    print("[!] Scan stopped by user.")

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

    # Shut down the CAN bus once only.
    #
    # The bus is not shut down inside the session loop.

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
                f"[!] Error while shutting down "
                f"the CAN interface: {error}"
            )

        finally:

            bus = None


# ====================================================
# Final Summary
# ====================================================

print()
print("=" * 60)
print("UDS Service Enumeration Completed")
print("=" * 60)

if not all_results:

    print(
        "No session scan was completed."
    )

else:

    for result_data in all_results.values():

        display_service_results(
            result_data["session_id"],
            result_data["services"]
        )