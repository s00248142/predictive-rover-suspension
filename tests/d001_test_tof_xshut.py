import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)          # /dev/spidev0.0
spi.max_speed_hz = 100000
spi.mode = 0
spi.cshigh = True

def write595(value):
    spi.xfer2([value & 0xFF]) # Mask for 74H595 shift register.

# Outputs: QB QC QD QE
S1 = 0x02
S2 = 0x04
S3 = 0x08
S4 = 0x10

try:
    while True:
        for v in [0x00, S1, S2, S3, S4, S1|S2|S3|S4]:
            print(hex(v))
            write595(v)
            time.sleep(0.5)
finally:
    write595(0x00)
    spi.close()