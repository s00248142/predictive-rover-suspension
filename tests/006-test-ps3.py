import pygame
import time

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

DPAD = {
    "UP": 13,
    "DOWN": 14,
    "LEFT": 15,
    "RIGHT": 16,
}

print("Controller:", js.get_name())
print("Reading D-pad (Ctrl+C to quit)\n")

try:
    while True:
        pygame.event.pump()

        for name, idx in DPAD.items():
            if js.get_button(idx):
                print("D-pad:", name)

        time.sleep(0.05)
except KeyboardInterrupt:
    pass
    