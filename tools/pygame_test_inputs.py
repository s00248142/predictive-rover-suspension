import time
import pygame

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

print("Controller:", js.get_name())
print("Axes:", js.get_numaxes())
print("Buttons:", js.get_numbuttons())
print("Hats:", js.get_numhats())
print()

while True:
    pygame.event.get()

    print("\033c", end="")  # clear terminal
    print("Move/press one control at a time")
    print("Controller:", js.get_name())
    print()

    print("AXES")
    for i in range(js.get_numaxes()):
        print(f"axis {i}: {js.get_axis(i): .3f}")

    print("\nBUTTONS")
    for i in range(js.get_numbuttons()):
        print(f"button {i}: {js.get_button(i)}")

    print("\nHATS / DPAD")
    for i in range(js.get_numhats()):
        print(f"hat {i}: {js.get_hat(i)}")

    time.sleep(0.1)