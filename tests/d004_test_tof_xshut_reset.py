import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)          # /dev/spidev0.0
spi.max_speed_hz = 100000
spi.mode = 0
spi.cshigh = True
spi.xfer2([0xFF]) # Reset shift register so all outputs are off (all xshut off)
spi.close()