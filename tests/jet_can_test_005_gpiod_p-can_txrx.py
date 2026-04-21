import subprocess
import time
import gpiod
import can

def run_cmd(cmd):
    print("Running:", cmd)
    subprocess.run(cmd, check=True)


# gpio_process = None # For Shell as background process
gpio_request = None # For gpiod as object showing ownership of pin (GPIO line)
# cangen_process = None


try:
    gpio_request = gpiod.request_lines(
        "/dev/gpiochip0",
        config={
        43: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT,
                            # Enable CAN0 by setting GPIO line 43 low
                            output_value=gpiod.line.Value.INACTIVE
                            )
        },
        consumer="can_app")

    print("GPIO line 43 held low. can0 enabled.")


    run_cmd(["sudo", "ip", "link", "set", "can0", "down"])
    run_cmd(["sudo", "ip", "link", "set", "can0", "type", "can", "bitrate", "1000000"])
    run_cmd(["sudo", "ip", "link", "set", "can0", "up"])

    print("can0 set to 1Mbps.")

    
    bus0 = None # Pre-contition for cleanup later
    # Attach bus0 object to can0
    bus0 = can.interface.Bus(channel="can0", interface="socketcan")

    # msg = can.Message(
    #     arbitration_id=0x123,
    #     data=[1, 2, 3, 4, 5, 6, 7, 8],
    #     is_extended_id=False
    # )

    # bus0.send(msg)

    # cangen_process = subprocess.Popen(
    # ["cangen", "can0", "-g", "1000", "-I", "123", "-L", "8"]
    # )

    count = 0
    
    while True:
        # msg = can.Message(
        #     arbitration_id=0x123,
        #     data=[count,0,0,0,0,0,0,0],
        #     is_extended_id=False
        # )

        # bus0.send(msg)

        # count = (count + 1) % 256

        # time.sleep(1)

        rx_msg = bus0.recv(timeout=1)
        if rx_msg is not None:
            print(rx_msg)
            bus0.send(
                can.Message(
                    arbitration_id=0x123,
                    data=[253,0,0,0,0,0,0,0],
                    is_extended_id=False)
            )


finally:
    print("Cleaning up...")

    # if gpio_process is not None:
    #     gpio_process.kill()
    #     gpio_process.wait()

    # if cangen_process is not None:
    #     cangen_process.kill()
    #     cangen_process.wait()

    try:
        run_cmd(["sudo", "ip", "link", "set", "can0", "down"])
    except Exception:
        pass

    if gpio_request is not None:
        gpio_request.release() # Release ownership of line 43.
    if bus0 is not None:
        bus0.shutdown()