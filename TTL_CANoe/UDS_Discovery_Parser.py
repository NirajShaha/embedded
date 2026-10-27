import os
import sys
from PIL import Image, ImageDraw, ImageFont


def extract_payload(fields):
    """
    Supports BOTH:

    CANFD:
    CANFD ... 8 8 02 10 01 00 00 00 00 00

    CAN:
    4A1 Tx d 8 02 10 01 00 00 00 00 00
    """

    #################################################
    # CAN FD FORMAT
    #
    # ... 8 8 02 10 01 ...
    #################################################

    for i in range(len(fields) - 1):

        if fields[i] == "8" and fields[i + 1] == "8":

            return [
                x.upper()
                for x in fields[i + 2:i + 10]
            ]

    #################################################
    # CAN FORMAT
    #
    # ... d 8 02 10 01 ...
    #################################################

    for i in range(len(fields) - 1):

        if (
            fields[i].lower() == "d"
            and fields[i + 1] == "8"
        ):

            return [
                x.upper()
                for x in fields[i + 2:i + 10]
            ]

    return []


def extract_can_id(fields):
    """
    Extract CAN ID from both
    CANFD and CAN logs.
    """

    try:

        #################################################
        # CAN FD
        #
        # CANFD 1 Rx 767 ...
        #################################################

        if "CANFD" in fields:

            return fields[4].upper()

        #################################################
        # STANDARD CAN
        #
        # 239.858666 1 4A1 Tx d 8 ...
        #################################################

        if (
            len(fields) > 4
            and fields[3] in ["Tx", "Rx"]
        ):

            return fields[2].upper()

    except:
        pass

    return None


def discover_diagnostic_ids(logfile):

    source_id = None
    destination_id = None

    with open(
        logfile,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        for line in file:

            fields = line.strip().split()

            if len(fields) < 5:
                continue

            can_id = extract_can_id(fields)

            if not can_id:
                continue

            payload = extract_payload(fields)

            if len(payload) < 3:
                continue

            payload = [
                x.upper()
                for x in payload
            ]

            #################################################
            # REQUEST
            #
            # Example:
            # 02 10 01
            #################################################

            if (
                payload[1] == "10"
                and payload[2] == "03"
            ):

                source_id = "0x" + can_id

            #################################################
            # POSITIVE RESPONSE
            #
            # Example:
            # 06 50 01
            #################################################

            elif (
                payload[1] == "50"
                and payload[2] == "03"
            ):

                if source_id:

                    destination_id = "0x" + can_id
                    break

    return source_id, destination_id


def save_table_to_screenshot(
        raw_table_lines,
        header_text,
        output_image_path):
    """
    Renders the clean table without
    console padding.
    """

    bg_color = (255, 255, 255)

    text_color = (20, 20, 20)

    font_size = 22

    line_height = 30

    image_lines = [header_text.strip()]

    for line in raw_table_lines:

        image_lines.append(line)

    img_width = 550

    img_height = (
        len(image_lines)
        * line_height
    ) + 40

    img = Image.new(
        'RGB',
        (img_width, img_height),
        color=bg_color
    )

    canvas = ImageDraw.Draw(img)

    try:

        font = ImageFont.truetype(
            "consola.ttf",
            font_size
        )

    except IOError:

        font = ImageFont.load_default()

    y_position = 20

    for line in image_lines:

        canvas.text(
            (20, y_position),
            line,
            fill=text_color,
            font=font
        )

        y_position += line_height

    try:

        img.save(output_image_path)

        print(
            f"Screenshot successfully saved to: "
            f"{output_image_path}"
        )

    except Exception as e:

        print(
            f"Error saving screenshot file: {e}"
        )


def process_and_generate_output(
        source,
        destination,
        screenshot_path):

    console_width = 100

    if source and destination:

        table = [

            "+----------------+------------------------+",
            "|     Identified Diagnostic CAN ID        |",
            "+----------------+------------------------+",
            "|     Source     |      Destination       |",
            "+----------------+------------------------+",
            "|{:^16}|{:^24}|".format(
                source,
                destination
            ),
            "+----------------+------------------------+"

        ]

    else:

        table = [

            "+-----------------------------------------+",
            "|   No diagnostic CAN IDs discovered.     |",
            "+-----------------------------------------+"

        ]

    padding = (
        console_width
        - len(table[0])
    ) // 2

    header_text = (
        "Enumerated Diagnostic CAN ID:"
    )

    print("")
    print(
        " " * padding +
        header_text
    )

    for row in table:

        print(
            " " * padding +
            row
        )

    print("")

    save_table_to_screenshot(
        table,
        header_text,
        screenshot_path
    )


def main():

    logfile = r"C:\Users\LDESHPAN\Favorites\Desktop\PythonScripts\Temp\TTL_CANoe\Source_and_Destination_Id_20260907_191905.asc"

    screenshot_output = (
        r"C:\Users\LDESHPAN\Favorites\Desktop\PythonScripts\Temp\TTL_CANoe\Source_and_Destination_Id_20260907_191905.png"
    )

    if not os.path.exists(logfile):

        print(
            "Log file not found:",
            logfile
        )

        return

    source, destination = (
        discover_diagnostic_ids(
            logfile
        )
    )

    process_and_generate_output(
        source,
        destination,
        screenshot_output
    )


if __name__ == "__main__":
    main()