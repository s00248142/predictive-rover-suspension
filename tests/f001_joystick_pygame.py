import pygame

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

print("Connected:", js.get_name())

while True:
    pygame.event.pump()

    lx = js.get_axis(0)  # left/right
    ly = js.get_axis(1)  # forward/back

    print(f"LX: {lx:.2f}, LY: {ly:.2f}")