import spidev, time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 100000
spi.mode = 0

# while True:
#     spi.xfer2([0xAA] * 100)
#     time.sleep(0.01)

while True:
    spi.xfer2([0x00] * 100)

# while True:
#     spi.xfer2([0xFF] * 100)