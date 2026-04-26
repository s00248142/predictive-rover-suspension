# /home/user/code/predictive-rover-suspension/tools/xshut_startup.py
import time
import spidev

spi = spidev.SpiDev()
spi.open(0, 0)          # /dev/spidev0.0
spi.max_speed_hz = 100000
spi.mode = 0
spi.xfer2([0x00]) # Reset shift register. All outputs off (all xshut off)
spi.close()
time.sleep(0.05) # Allow signals to fully drop off