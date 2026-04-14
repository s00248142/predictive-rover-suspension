from gpiozero import LED, Device
led = LED(17)          # or any GPIO number
print(Device.pin_factory) # Show what GPIOZERO selects lgpio, gpiod(native), etc
led.close()