from bus_manager import bus
import can
import tkinter as tk
from tkinter import ttk, messagebox


class CANMessageSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vector CAN Message Sender")
        self.root.geometry("500x420")
        self.root.resizable(False, False)

        # Apply a clean theme
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Main Layout Frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- CAN Config Controls ---
        # DLC
        ttk.Label(main_frame, text="DLC (Data Length Code):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.dlc_spinbox = ttk.Spinbox(
            main_frame, from_=0, to=8, width=10, state="readonly"
        )
        self.dlc_spinbox.set(8)  # Default DLC = 8
        self.dlc_spinbox.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Arbitration ID
        ttk.Label(main_frame, text="Arbitration ID (Hex, e.g., 471):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.arb_id_entry = ttk.Entry(main_frame, width=15)
        self.arb_id_entry.insert(0, "471")
        self.arb_id_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Extended ID Checkbox
        self.is_extended_var = tk.BooleanVar(value=False)
        self.extended_chk = ttk.Checkbutton(
            main_frame,
            text="Extended Frame (29-bit ID)",
            variable=self.is_extended_var,
        )
        self.extended_chk.grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # Data Bytes Section Header
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=15
        )
        ttk.Label(
            main_frame, text="Data Bytes (Hex 00 - FF):", font=("Helvetica", 10, "bold")
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Data Entry Inputs Frame
        data_frame = ttk.Frame(main_frame)
        data_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Default Data Payload: [0x03, 0x22, 0xF1, 0x8C, 0x00, 0x00, 0x00, 0x00]
        default_payload = ["03", "22", "F1", "8C", "00", "00", "00", "00"]
        self.data_entries = []

        for i in range(8):
            lbl = ttk.Label(data_frame, text=f"B{i}")
            lbl.grid(row=0, column=i, padx=2)

            entry = ttk.Entry(data_frame, width=4, justify="center")
            entry.insert(0, default_payload[i])
            entry.grid(row=1, column=i, padx=2)
            self.data_entries.append(entry)

        # --- Submit Action Button ---
        self.send_btn = ttk.Button(
            main_frame, text="Send CAN Message", command=self.send_can_message
        )
        self.send_btn.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")

        # --- Status Output Console ---
        self.status_label = ttk.Label(
            main_frame, text="Status: Ready", foreground="blue"
        )
        self.status_label.grid(row=7, column=0, columnspan=2, sticky=tk.W)

    def parse_inputs(self):
        """Validates and extracts parameters from UI elements."""
        # 1. DLC Validation
        dlc = int(self.dlc_spinbox.get())

        # 2. Arbitration ID Validation
        raw_arb_id = self.arb_id_entry.get().strip()
        if not raw_arb_id:
            raise ValueError("Arbitration ID field cannot be empty.")
        try:
            arb_id = int(raw_arb_id, 16)
        except ValueError:
            raise ValueError(
                f"Invalid Arbitration ID '{raw_arb_id}'. Must be a valid Hexadecimal number."
            )

        # Validate Extended vs Standard ID range constraints
        is_extended = self.is_extended_var.get()
        if is_extended and (arb_id < 0 or arb_id > 0x1FFFFFFF):
            raise ValueError(
                "Extended ID must be between 0x00000000 and 0x1FFFFFFF."
            )
        elif not is_extended and (arb_id < 0 or arb_id > 0x7FF):
            raise ValueError(
                "Standard ID must be between 0x000 and 0x7FF (11-bit limit)."
            )

        # 3. Data Payloads Parsing (up to DLC length)
        data_bytes = []
        for i in range(dlc):
            raw_byte = self.data_entries[i].get().strip()
            if not raw_byte:
                raise ValueError(f"Data byte entry B{i} is empty.")
            try:
                byte_val = int(raw_byte, 16)
                if not (0 <= byte_val <= 255):
                    raise ValueError
            except ValueError:
                raise ValueError(
                    f"Invalid Byte at position B{i}: '{raw_byte}'. Must be a 2-digit Hex value (00 to FF)."
                )
            data_bytes.append(byte_val)

        return dlc, arb_id, data_bytes, is_extended

    def send_can_message(self):
        """Backend Handler: Parses input, instantiates Vector bus connection, sends msg, and closes handle."""
        try:
            # Step 1: Input Validation
            dlc, arb_id, data_payload, is_extended = self.parse_inputs()

            # Step 2: Bus Initialization
            # Note: Vector drivers must be installed on the system (vxlapi.dll)
            bus = can.Bus(interface="vector", channel=0, app_name="Python")

            # Step 3: Message Construction
            msg = can.Message(
                dlc=dlc,
                arbitration_id=arb_id,
                data=data_payload,
                is_extended_id=is_extended,
            )

            # Step 4: Transmission and Resource Teardown
            bus.send(msg)
            bus.shutdown()

            # Update Interface Status
            formatted_hex_data = " ".join([f"{b:02X}" for b in data_payload])
            self.status_label.config(
                text=f"Status: Sent ID=0x{arb_id:X} Data=[{formatted_hex_data}]",
                foreground="green",
            )

        except can.CanError as e:
            # Captures low-level Vector driver / Hardware interface faults
            self.status_label.config(
                text="Status: Vector Bus Error", foreground="red"
            )
            messagebox.showerror("CAN Interface Error", f"Failed to send on Vector Channel:\n{e}")

        except ValueError as e:
            # Captures user input validation faults
            self.status_label.config(
                text="Status: Input Validation Error", foreground="red"
            )
            messagebox.showerror("Invalid Input", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = CANMessageSenderApp(root)
    root.mainloop()