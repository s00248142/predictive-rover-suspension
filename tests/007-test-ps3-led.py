import pygame
# import time
from time import sleep
from gpiozero import LED, Device

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

led = LED(25)

DPAD = {
    "UP": 13,
    "DOWN": 14,
    "LEFT": 15,
    "RIGHT": 16,
}

for i in range(0,4):
    led.on()
    sleep(0.25)
    led.off()
    sleep(0.25)
    i = i+1

print("Controller:", js.get_name())
print("Reading D-pad (Ctrl+C to quit)\n")

try:
    while True:
        pygame.event.pump()

        for name, idx in DPAD.items():
            if js.get_button(idx):
                print("D-pad:", name)
                if name=="UP":
                    led.on()
                else:
                    led.off()

        sleep(0.05)
except KeyboardInterrupt:
    pass
    