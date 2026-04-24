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

# Bind SetRangeTiming
lib.VL53L4CD_SetRangeTiming.argtypes = [c.c_uint16, c.c_uint32, c.c_uint32]
lib.VL53L4CD_SetRangeTiming.restype = c.c_uint8
############################## End of Bindings ###############################

# Assign variables
device = c.c_uint16(0x29) # Device I2C address
ready = c.c_uint8(0) # Initialise ready.value as 0
results = ResultsData() # Empty struct

# Initialise sensor
status = lib.VL53L4CD_SensorInit(device)
print("SensorInit:", status)

# Set sensor timing (device, timing_budget_ms, inter_measurement_ms )
status = lib.VL53L4CD_SetRangeTiming(device, 20, 0) # 20ms timing budget
print("SetRangeTiming:", status)

# Start ranging on the sensor
status = lib.VL53L4CD_StartRanging(device)
print("StartRanging:", status)

###################### Continuous measurement polling loop #####################

count = 0
t0 = time.perf_counter() # Used to calculate frequency of loop. 

while True:
    ready.value = 0

    # Check for data_ready interrupt flag.
    # Note: byref(ready) is equivalent to &ready in C. Gets address.
    while ready.value != 1:
        status = lib.VL53L4CD_CheckForDataReady(device,c.byref(ready))
        if status != 0:
            raise RuntimeError(f"CheckForDataReady failed: {status}")
        time.sleep(0.002)

    # Get results data from sensor
    status = lib.VL53L4CD_GetResult(device, c.byref(results))
    if status != 0:
        raise RuntimeError(f"GetResult failed: {status}")

    # Clear interrupt flag
    status = lib.VL53L4CD_ClearInterrupt(device)
    if status != 0:
        raise RuntimeError(f"ClearInterrupt failed: {status}")
    
    # Print results
    print(f"distance = {results.distance_mm} mm, "
            f"sigma = {results.sigma_mm} mm")
    
    # Calculate loop rate in Hz
    count += 1
    now = time.perf_counter()

    # Print loop frequency once per second
    if now - t0 >= 1.0:
        print(f"rate = {count / (now - t0):.1f} Hz")
        
        # Reset rate timer
        count = 0
        t0 = now






