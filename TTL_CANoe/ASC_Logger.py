from datetime import datetime


class ASCLogger:

    def __init__(self):

        self.file = None

        self.first_timestamp = None

        self.filters = None

    def start_log(

            self,

            testcase_name,

            filters=None

    ):

        """

        filters example:


        filters=[0x471,0x479]

        """

        self.filters = filters

        filename = (

                testcase_name

                + "_"

                + datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )

                + ".asc"

        )

        self.file = open(

            filename,

            "w",

            encoding="utf-8"

        )

        now = datetime.now()

        self.file.write(

            f"date {now}\n"

        )

        self.file.write(

            "base hex timestamps absolute\n\n"

        )

    def log_frame(

            self,

            msg,

            direction

    ):

        if self.file is None:
            return

        # --------------------------------------------------

        # ID Filter

        # --------------------------------------------------

        if self.filters is not None:

            if msg.arbitration_id not in self.filters:
                return

        # --------------------------------------------------

        # Relative CANoe Timestamp

        # --------------------------------------------------

        if self.first_timestamp is None:
            self.first_timestamp = msg.timestamp

        relative_timestamp = (

                msg.timestamp

                - self.first_timestamp

        )

        frame_type = (

            "fd"

            if msg.is_fd

            else "d"

        )

        data_text = " ".join(

            f"{b:02X}"

            for b in msg.data

        )

        self.file.write(

            f"{relative_timestamp:10.6f} "

            f"1 "

            f"{msg.arbitration_id:03X} "

            f"{direction:2} "

            f"{frame_type} "

            f"{len(msg.data)} "

            f"{data_text}\n"

        )

        self.file.flush()

    def stop_log(self):

        if self.file:
            self.file.close()

            self.file = None
