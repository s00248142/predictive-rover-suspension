# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

# Simple demo of the VL53L4CD distance sensor.
# Will print the sensed range/distance every second.

import board
import digitalio # From CircuitPython library
import adafruit_vl53l4cd

i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
# PIN = board.D18
vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)
# led = digitalio.DigitalInOut(PIN)
# led.direction = digitalio.Direction.OUTPUT

# OPTIONAL: can set non-default values
vl53.inter_measurement = 0
vl53.timing_budget = 10

print("VL53L4CD Simple Test.")
print("--------------------")
model_id, module_type = vl53.model_info
print(f"Model ID: 0x{model_id:0X}")
print(f"Module Type: 0x{module_type:0X}")
print(f"Timing Budget: {vl53.timing_budget}")
print(f"Inter-Measurement: {vl53.inter_measurement}")
print("--------------------")

vl53.start_ranging()

while True:
    while not vl53.data_ready:
        pass
    vl53.clear_interrupt()
    print(f"Distance: {vl53.distance} cm")
    # if vl53.distance < 15 and vl53.distance > 0.1:
    #     led.value = True
    # else:
    #     led.value = False

