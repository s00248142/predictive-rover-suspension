# 'ctypes' is standard Python module that interacts with 
# Linux shared object libraries (*.so files), and C libraries generally.
import ctypes as c 
import time
import tof

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



tof1 = tof.TofSensor(tof_idx=1)
# Assign variables
device = tof1.addr # Device I2C address (already wrapped as c_uint16 in class)
ready = c.c_uint8(0) # Initialise ready.value as 0
results = ResultsData() # Empty struct

# Initialise sensor
status = lib.VL53L4CD_SensorInit(device)
print("SensorInit:", status)

# Set sensor timing (device, timing_budget_ms, inter_measurement_ms )
timing_budget_ms = 20
status = lib.VL53L4CD_SetRangeTiming(device, timing_budget_ms, 0) # 20ms timing budget
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
    # print(f"distance = {results.distance_mm} mm, "
    #         f"sigma = {results.sigma_mm} mm")

    # Store results
    latest_distance = results.distance_mm
    latest_sigma = results.sigma_mm
    latest_status = results.range_status
    
    # Calculate loop rate in Hz
    count += 1
    now = time.perf_counter()

    # Print loop frequency once per second
    elapsed = now - t0
    if elapsed >= 2.0:
        hz = count / elapsed

        print(f"device=0x{device.value:02x}",
            f"rate={hz:.1f} Hz, "
            f"distance={latest_distance} mm, "
            f"sigma={latest_sigma} mm, "
            f"status={latest_status}"
        )
        
        # Reset rate timer
        count = 0
        t0 = now

    time.sleep((timing_budget_ms-5)/1000) # Block function to avoid hogging resources.