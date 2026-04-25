import spidev

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 100000
spi.mode = 0

tests = [0x00, 0x55, 0xAA, 0xFF]

for value in tests:
    received = spi.xfer2([value])[0]
    print(hex(value), "->", hex(received))

spi.close()