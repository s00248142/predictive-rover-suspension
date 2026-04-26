
import ctypes as c 

# Intent:
old = 0x2A
new = 0x29

# Shared library 
lib = c.CDLL("./tof_driver/libvl53l4cd.so")

# Bind GetSensorId
lib.VL53L4CD_GetSensorId.argtypes = [c.c_uint16, c.POINTER(c.c_uint16)]
lib.VL53L4CD_GetSensorId.restype = c.c_uint8

# Bind SetI2CAddress
lib.VL53L4CD_SetI2CAddress.argtypes = [c.c_uint16, c.c_uint8]
lib.VL53L4CD_SetI2CAddress.restype = c.c_uint8

# Fill in the details required
old_device = c.c_uint16(old)
new_linux_addr = new
new_st_addr = c.c_uint8(new_linux_addr << 1)

status = lib.VL53L4CD_SetI2CAddress(old_device, new_st_addr)
print("SetI2CAddress:", status)

new_device = c.c_uint16(new_linux_addr)
sensor_id = c.c_uint16(0)

status = lib.VL53L4CD_GetSensorId(new_device, c.byref(sensor_id))
print("status:", status)
print(f"sensor_id: 0x{sensor_id.value:04x}")

