PACKET_COUNT = 100


def main() -> None:
    print(f"Starting simulated send of {PACKET_COUNT} data packets")
    for packet_number in range(1, PACKET_COUNT + 1):
        print(f"[SEND] Packet {packet_number:03d}/{PACKET_COUNT}: data packet")
    print("Finished sending data packets")


if __name__ == "__main__":
    main()
