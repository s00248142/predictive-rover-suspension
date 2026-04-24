import ctypes as c

lib = c.CDLL("./tof_driver/libvl53l4cd.so")

lib.VL53L4CD_GetSensorId.argtypes = [c.c_uint16, c.POINTER(c.c_uint16)]
lib.VL53L4CD_GetSensorId.restype = c.c_uint8

device = c.c_uint16(0x29)
sensor_id = c.c_uint16(0)

status = lib.VL53L4CD_GetSensorId(device, c.byref(sensor_id))

print(f"status = {status}")
print(f"sensor_id = 0x{sensor_id.value:04x}")