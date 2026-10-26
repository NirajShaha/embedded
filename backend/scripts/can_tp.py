import can

TX_ID = 0x471

class CanTp:

    def __init__(self, bus):

        self.bus = bus

        self.reset()

    def reset(self):

        self.active = False
        self.total_length = 0
        self.buffer = bytearray()
        self.expected_sn = 1

    def send_fc(self, rx_msg):

        fc = can.Message(
            arbitration_id=TX_ID,
            is_extended_id=False,
            is_fd=rx_msg.is_fd,
            bitrate_switch=(
                rx_msg.bitrate_switch
                if rx_msg.is_fd
                else False
            ),
            data=[
                0x30,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00
            ]
        )

        self.bus.send(fc)

        return fc

    def process(self, msg):

        if len(msg.data) == 0:
            return None

        pci_type = msg.data[0] >> 4

        # Single Frame
        if pci_type == 0:
            return None

        # First Frame
        if pci_type == 1:

            self.total_length = (
                ((msg.data[0] & 0x0F) << 8)
                | msg.data[1]
            )

            self.buffer = bytearray(msg.data[2:])

            self.expected_sn = 1

            self.active = True

            fc_msg = self.send_fc(msg)

            return fc_msg

        # Consecutive Frame
        if pci_type == 2:

            if not self.active:
                return None

            sn = msg.data[0] & 0x0F

            if sn != self.expected_sn:

                self.reset()

                return None

            self.buffer.extend(msg.data[1:])

            self.expected_sn = (
                self.expected_sn + 1
            ) & 0x0F

            if len(self.buffer) >= self.total_length:

                self.reset()

            return None

        return None