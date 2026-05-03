import pygame, time

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0)
js.init()
time.sleep(1)

print("axes:", js.get_numaxes(), "buttons:", js.get_numbuttons(), "hats:", js.get_numhats())

while True:
    pygame.event.pump()
    hats = [js.get_hat(i) for i in range(js.get_numhats())]
    axes = [round(js.get_axis(i), 3) for i in range(js.get_numaxes())]
    buttons = [js.get_button(i) for i in range(js.get_numbuttons())]
    print("hats:", hats, "axes:", axes, "buttons:", buttons)
    time.sleep(2)
