import pygame
from time import sleep
from gpiozero import LED, Device, CamJamKitRobot

pygame.init()
pygame.joystick.init()
js = pygame.joystick.Joystick(0)
js.init()

led = LED(25)
robot = CamJamKitRobot()

for i in range(0,4):
    led.on()
    sleep(0.25)
    led.off()
    sleep(0.25)
    i = i+1

buttons = [js.get_button(i) for i in range(js.get_numbuttons())]

while buttons[2] == 0: # Exit program by pressing the Triangle button on DS3
    pygame.event.pump()

    axes = [round(js.get_axis(i), 3) for i in range(js.get_numaxes())] # 3 decimal places
    buttons = [js.get_button(i) for i in range(js.get_numbuttons())]


    if axes[5] > -0.9:
        robot.forward(speed=1, curve_right=0)
    elif axes[2] > -0.9:
        robot.backward(speed=1, curve_right=0)
    else:
        robot.stop()

    # Use X button to turn on blue LED, O to turn off blue LED
    if buttons[0] == 1:
        led.on()
    elif buttons[1] ==1:
        led.off()
    
    # Loop frequency
    sleep(0.1)
