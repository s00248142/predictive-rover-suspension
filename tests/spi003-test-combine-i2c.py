import time
import spidev
import board
import adafruit_vl53l4cd

ANGLE_REG = 0x3FFF  # angle register (14-bit address space)
READ_BIT  = 1 << 14
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)

def even_parity_15bits(x: int) -> int:
    # parity over bits 0..14, parity bit is bit15 so that total #ones is even
    ones = bin(x & 0x7FFF).count("1")
    return 0 if (ones % 2 == 0) else 1

def make_read_cmd(addr: int) -> int:
    cmd = (addr & 0x3FFF) | READ_BIT          # bits 13..0 addr, bit14=R
    cmd |= (even_parity_15bits(cmd) << 15)    # bit15 parity
    return cmd

def xfer16(spi: spidev.SpiDev, word: int) -> int:
    hi = (word >> 8) & 0xFF
    lo = word & 0xFF
    rx = spi.xfer2([hi, lo])
    return (rx[0] << 8) | rx[1]

# OPTIONAL: can set non-default values
vl53.inter_measurement = 0
vl53.timing_budget = 200

vl53.start_ranging()

spi = spidev.SpiDev()
spi.open(0, 0)                 # CE0 (/dev/spidev0.0)
spi.max_speed_hz = 1_000_000
spi.mode = 0b01                # SPI mode 1 per datasheet :contentReference[oaicite:1]{index=1}
spi.bits_per_word = 8

read_angle_cmd = make_read_cmd(ANGLE_REG)

try:
    while True:
        # AS5048A returns data for the *previous* command,
        # so do a "command frame" then a "dummy frame" to read the result.
        xfer16(spi, read_angle_cmd)          # prime
        raw = xfer16(spi, 0x0000)            # read response

        err = (raw >> 14) & 0x1              # error flag
        angle14 = raw & 0x3FFF               # 14-bit angle
        deg = angle14 * 360.0 / 16384.0

        vl53.clear_interrupt()

        print(f"raw=0x{raw:04X} err={err} angle={angle14} deg={deg:.2f} Distance: {vl53.distance} cm")
        time.sleep(0.5)

except KeyboardInterrupt:
    pass
finally:
    spi.close()