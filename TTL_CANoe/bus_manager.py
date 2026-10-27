import can

bus = can.Bus(
    interface="vector",
    channel=0,
    app_name="Python",
    fd=True,
    bitrate=500000,
    dbitrate=2000000,
    receive_own_messages=True
)
