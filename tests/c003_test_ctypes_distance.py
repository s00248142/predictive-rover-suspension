# 'ctypes' is standard Python module that interacts with 
# Linux shared object libraries (*.so files), and C libraries generally.
import ctypes as c 
import time

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

# Shared library compiled in GCC from platform.c and VL53L4CD_api.c
lib = c.CDLL("./tof_driver/libvl53l4cd.so")

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
############################## End of Bindings ###############################

# Assign variables
device = c.c_uint16(0x29) # Device I2C address
ready = c.c_uint8(0) # Initialise ready.value as 0

# Initialise sensor
status = lib.VL53L4CD_SensorInit(device)
print("SensorInit:", status)

# Start ranging on the sensor
status = lib.VL53L4CD_StartRanging(device)
print("StartRanging:", status)

# Check for data_ready interrupt flag.
# Note: byref(ready) is equivalent to &ready in C. Gets address.
while ready.value != 1:
    status = lib.VL53L4CD_CheckForDataReady(device,c.byref(ready))

print("status =", status)
print("ready =", ready.value)

results = ResultsData() # Empty struct

# Get results data from sensor
status = lib.VL53L4CD_GetResult(device, c.byref(results))

print("GetResult:", status)
print("distance_mm =", results.distance_mm)
print("range_status =", results.range_status)
print("sigma_mm =", results.sigma_mm)

# Clear interrupt flag
status = lib.VL53L4CD_ClearInterrupt(device)
print("ClearInterrupt:", status)




