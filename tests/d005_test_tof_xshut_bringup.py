import spidev
import time


tof_idx = 4 # Change this value for testing between 1 and 4.

xshut = [0, 1, 3, 7, 15] 

spi = spidev.SpiDev()
spi.open(0, 0)          # /dev/spidev0.0
spi.max_speed_hz = 100000
spi.mode = 0
# spi.cshigh = False
# time.sleep(0.02)
# Outputs: QB QC QD QE, so index << 1
# spi.xfer2([(tof_idx +1) & 0xFF]) # Mask for 74H595 shift register.
spi.xfer2([(xshut[tof_idx] << 1) & 0xFF])
spi.close()
# time.sleep(0.02)