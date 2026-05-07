
'''
********************************************************************************
* File Name: xshut_startup.py
* Description: Ensure each shift register for contolling XSHUT is low at init. 
*   Without this startup function the 74HC595 will turn on all ToF sensors
*   at the same time, making address changes impossible.
* Programmer: Alan Ryan (s00248142)
* Date: 06/04/2025
* Version: 1.0
********************************************************************************
'''
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