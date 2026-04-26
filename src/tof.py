
import ctypes as c 

# Shared library compiled in GCC from platform.c and VL53L4CD_api.c
lib = c.CDLL("./tof_driver/libvl53l4cd.so")

# Pool of available addresses
addr_pool = [None, 0x2A, 0x2B, 0x2C, 0x2D] # Program picks between 1 and 4

# Replicate VL53L4CD_ResultsData_t struct from VL53L4CD_api.h
class ResultsData(c.Structure):
    _fields_ = [
        ("range_status", c.c_uint8),
        ("distance_mm", c.c_uint16),
        ("ambient_rate_kcps", c.c_uint32),
        ("ambient_per_spad_kcps", c.c_uint32),
        ("signal_rate_kcps", c.c_uint32),
        ("signal_per_spad_kcps", c.c_uint32),
        ("number_of_spad", c.c_uint16),
        ("sigma_mm", c.c_uint16),
    ]

############################## Function Bindings ###############################
# Bind SensorInit
lib.VL53L4CD_SensorInit.argtypes = [c.c_uint16] # Input parameter types as list
lib.VL53L4CD_SensorInit.restype = c.c_uint8 # Return type (status = 0, etc...)

# Bind StartRanging
lib.VL53L4CD_StartRanging.argtypes = [c.c_uint16]
lib.VL53L4CD_StartRanging.restype = c.c_uint8

# Bind CheckForDataReady
lib.VL53L4CD_CheckForDataReady.argtypes = [c.c_uint16, c.POINTER(c.c_uint8)]
lib.VL53L4CD_CheckForDataReady.restype = c.c_uint8

# Bind GetResult
lib.VL53L4CD_GetResult.argtypes = [c.c_uint16, c.POINTER(ResultsData)]
lib.VL53L4CD_GetResult.restype = c.c_uint8

# Bind ClearInterrupt
lib.VL53L4CD_ClearInterrupt.argtypes = [c.c_uint16]
lib.VL53L4CD_ClearInterrupt.restype = c.c_uint8

# Bind SetRangeTiming
lib.VL53L4CD_SetRangeTiming.argtypes = [c.c_uint16, c.c_uint32, c.c_uint32]
lib.VL53L4CD_SetRangeTiming.restype = c.c_uint8

# Bind GetSensorId
lib.VL53L4CD_GetSensorId.argtypes = [c.c_uint16, c.POINTER(c.c_uint16)]
lib.VL53L4CD_GetSensorId.restype = c.c_uint8

# Bind SetI2CAddress
lib.VL53L4CD_SetI2CAddress.argtypes = [c.c_uint16, c.c_uint8]
lib.VL53L4CD_SetI2CAddress.restype = c.c_uint8
############################## End of Bindings ###############################



# ToF Sensor class for VL53L4CD
class TofSensor:
    def __init__(self, tof_idx=0):
        self.tof_idx = tof_idx
        self.default_addr = 0x29
        self.addr = 0x00
        self.change_addr()
        self.results = ResultsData()

    def change_addr(self):
        if self.tof_idx == 0:
            raise ValueError("0 is placeholder. Use sensor IDs starting at 1.")

        old_addr = c.c_uint16(self.default_addr)
        new_linux_addr = addr_pool[self.tof_idx]
        new_st_addr = c.c_uint8(new_linux_addr << 1)

        status = lib.VL53L4CD_SetI2CAddress(old_addr, new_st_addr)
        print("VL53L4CD_SetI2CAddress() status:", status)

        self.addr = c.c_uint16(new_linux_addr)
        sensor_id = c.c_uint16(0)

        status = lib.VL53L4CD_GetSensorId(self.addr, c.byref(sensor_id))
        print("VL53L4CD_GetSensorId() status:", status)
        print("New I2C address:", hex(new_linux_addr))
        print(f"sensor_id: 0x{sensor_id.value:04x}")