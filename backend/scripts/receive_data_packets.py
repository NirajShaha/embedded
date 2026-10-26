PACKET_COUNT = 100


def main() -> None:
    print(f"Starting simulated receive of {PACKET_COUNT} data packets")
    for packet_number in range(1, PACKET_COUNT + 1):
        print(f"[RECEIVE] Packet {packet_number:03d}/{PACKET_COUNT}: data packet")
    print("Finished receiving data packets")


if __name__ == "__main__":
    main()
