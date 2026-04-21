from smbus2 import SMBus

bus = SMBus(1)        # /dev/i2c-1
addr = 0x29

value = bus.read_byte_data(addr, 0x00)
print(value)