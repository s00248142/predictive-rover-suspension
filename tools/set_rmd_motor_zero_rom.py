# Stores the current absolute encoder position as zero in ROM of RMD motor
# Use where required, after rebuild etc...
# This avoids issues between MIT span, RMD multi-turn, and RMD single-turn modes

import time
import can

can0 = can.Bus(
    interface='socketcan',
    channel='can0'
)

input("Ensure CAN traffic is quiet. Terminal command: candump -tz can0" \
        "\nPress Enter to confirm.")

motor_can_id = 0x144

''' 
Read Multi-Turn Encoder Position Data Command (0x60)
# Print current multi-turn encoder value message
# Reply example: can0  244   [8]  62 00 00 00 22 5F 37 00
# Last 4 bytes are the position as 32-bit split integer
'''
def print_multi_turn_position(timeout: float = 0.2):
        # Request current multi-turn position.
        encoder_read_request = can.Message( # Page 23 of manual
                arbitration_id=0x144, # Pre-defined address of RMD motor.
                data=[0x62, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
                is_extended_id=False
            )

        can0.send(encoder_read_request)

        # Block until message is received from motor (time-out of 0.2 seconds).
        start = time.time()
        while time.time() - start < timeout:
            msg = can0.recv(timeout=timeout) # Receive msg from python-can
            if msg is None:
                continue # Restart the loop
            if msg.arbitration_id != 0x244: # IDs must match
                continue
            if len(msg.data) < 8: # Eight bytes in a list
                continue
            # print(msg.data) # Uncomment to debug
            return msg.data

        raise TimeoutError("No RMD motion feedback frame received")

def send_and_wait(cmd: int, timeout: float = 0.2):
    msg = can.Message(
        arbitration_id=0x144,
        data=[cmd, 0, 0, 0, 0, 0, 0, 0],
        is_extended_id=False
    )

    can0.send(msg)

    start = time.time()

    while time.time() - start < timeout:
        remaining = timeout - (time.time() - start)
        reply = can0.recv(timeout=remaining)

        if reply is None:
            continue

        if reply.arbitration_id != 0x244:
            continue

        if len(reply.data) < 8:
            continue

        print("ACK:", reply.data.hex(" "))
        return reply.data

    raise TimeoutError(f"No reply for command 0x{cmd:02X}")

'''-------------------------------- App Code --------------------------------'''

# Observe the received message before setting the zero to ROM
print([hex(x) for x in print_multi_turn_position()])
input("Press Enter to save this position as zero to motor's ROM.")

# Save zero to ROM
cmd = 0x64 # Page 23 of manual
send_and_wait(cmd)

# set_zero = can.Message( # Page 23 of manual
#     arbitration_id=0x144, # Pre-defined address of RMD motor.
#     data=[0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
#     is_extended_id=False
# )

# can0.send(set_zero)

# Reset system (required)
reset_system = can.Message( # Page 23 of manual
    arbitration_id=0x144, # Pre-defined address of RMD motor.
    data=[0x76, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    is_extended_id=False
)
can0.send(reset_system)

time.sleep(3) # Allow 3 seconds for system to restart.

# Observe the received message before setting the zero to ROM
print([hex(x) for x in print_multi_turn_position()])
input("Press Enter to finish.")
