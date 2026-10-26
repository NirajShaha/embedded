import time
import can

def scan_uds_ids(interface='can1', start_id=0x450, end_id=0x4A0, timeout=0.05):
    """
    Scans a range of CAN IDs to discover active UDS source and destination pairs.
    """
    print(f"[*] Starting UDS discovery scan on {interface}...")
    print(f"[*] Scanning ID range: {hex(start_id)} to {hex(end_id)}")
    print("-" * 50)

    try:
        # Initialize the CAN bus interface
        bus = can.interface.Bus(channel=interface, bustype='socketcan')
    except Exception as e:
        print(f"[-] Failed to initialize bus: {e}")
        return

    discovered_pairs = []

    # Iterate through the defined request ID range
    for request_id in range(start_id, end_id + 1):
        # Standard UDS message format: [PCI (Length), Service ID, Sub-function, ...]
        # 0x02: Remaining bytes length
        # 0x10: Diagnostic Session Control
        # 0x01: Default Session
        msg_data = [0x02, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
       
        msg = can.Message(
            arbitration_id=request_id,
            data=msg_data,
            is_extended_id=False
        )

        try:
            # Send the request
            bus.send(msg)
           
            # Listen for a response within the timeout window
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                rx_msg = bus.recv(timeout=0.01)
               
                if rx_msg is not None:
                    # Ignore messages sent by the script itself
                    if rx_msg.arbitration_id == request_id:
                        continue
                       
                    # Analyze response data for UDS behavior
                    # Positive response for service 0x10 is usually 0x50
                    if len(rx_msg.data) > 1 and rx_msg.data[1] == 0x50:
                        print(f"[+] Found Active ECU -> Request ID: {hex(request_id)} | Response ID: {hex(rx_msg.arbitration_id)}")
                        discovered_pairs.append((request_id, rx_msg.arbitration_id))
                        break
                    # Negative Response Code (NRC) checking (0x7F)
                    elif len(rx_msg.data) > 1 and rx_msg.data[1] == 0x7F:
                        print(f"[!] Found Responding ECU (NRC received) -> Request ID: {hex(request_id)} | Response ID: {hex(rx_msg.arbitration_id)}")
                        discovered_pairs.append((request_id, rx_msg.arbitration_id))
                        break

        except can.CanError as e:
            print(f"[-] Error transmitting on ID {hex(request_id)}: {e}")

    print("-" * 50)
    print(f"[*] Scan complete. Discovered {len(discovered_pairs)} active UDS pairs.")
    bus.shutdown()

if __name__ == "__main__":
    # Standard ISO 15765-4 physical request range for 11-bit IDs
    # For 29-bit extended IDs, typical ranges include 0x18DB33F1 (Functional)
    scan_uds_ids(interface='can1', start_id=0x450, end_id=0x4A0)