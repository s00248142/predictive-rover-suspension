# CamJam EduKit 3 - Robotics
# Worksheet 3 - Motor Test Code

from gpiozero import LED, Device
from time import sleep
from gpiozero import CamJamKitRobot  # Import the CamJam GPIO Zero Library
#from gpiozero.pins.native import NativeFactory
#Device.pin_factory = NativeFactory()

led = LED(25)
print(Device.pin_factory)
robot = CamJamKitRobot()
#robot = CamJamKitRobot(pwm=False)

# while True:
for i in range(0,4):
    led.on()
    sleep(0.25)
    led.off()
    sleep(0.25)
    i = i+1

# Turn the motors on
robot.forward(speed=0.5)

# Wait for 1 seconds
sleep(1)

# Turn the motors off
robot.stop()

# Wait for 1 seconds
sleep(0.5)

# Turn the motors on
robot.backward(speed=0.5)

# Wait for 1 seconds
sleep(1)

# Turn the motors off
robot.stop()
