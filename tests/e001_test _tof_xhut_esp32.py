import board
import digitalio
import time
import supervisor

pins = [board.D0, board.D1, board.D2, board.D3]

outs = []
for p in pins:
    x = digitalio.DigitalInOut(p)
    x.direction = digitalio.Direction.OUTPUT
    x.value = False
    outs.append(x)

def set_outputs(mask):
    for i, x in enumerate(outs):
        x.value = bool(mask & (1 << i))

print("Ready. Send 0-15.")

while True:
    if supervisor.runtime.serial_bytes_available:
        cmd = input().strip()

        try:
            value = int(cmd)
            if 0 <= value <= 15:
                set_outputs(value)
                print("set", value)
            else:
                print("use 0-15")
        except ValueError:
            print("bad:", cmd)

    time.sleep(0.01)