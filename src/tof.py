
import ctypes as c 
import time
import serial

# Shared library compiled in GCC from platform.c and VL53L4CD_api.c
lib = c.CDLL("./tof_driver/libvl53l4cd.so")

# Pool of available addresses
addr_pool = [None, 0x2A, 0x2B, 0x2C, 0x2D] # Program picks between 1 and 4

# Xshut sequence for powering on ToF sensors to change their volatile addresses
xshut = [0, 1, 3, 7, 15] # Nibbles [0000, 0001, 0011, 0111, 1111]

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
        self.expected_sensor_id = 0xebaa
        self.timing_budget_ms = 20
        self.intermeasurement_ms = 0
        self.ready = c.c_uint8(0) # Initialise ready.value as 0
        self.xshut_on()
        self.change_addr()
        self.results = ResultsData()
        self.init()

    def xshut_on(self):
        print(f"Attempting xshut turn on for sensor {self.tof_idx}")

        ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
        # time.sleep(2)

        # print(ser.read_all().decode(errors="ignore")

        # ser.write(b"15\n")
        for i in range(20):
            ser.write(f"{xshut[self.tof_idx]}\n".encode())
            ser.flush()

            time.sleep(0.05)

            # print("reply:")
            response = ser.read_all().decode(errors="ignore")
            if response == f"set {xshut[self.tof_idx]}":
                break
            elif i > 19:
                print(f"Timeout while turning on sensor {self.tof_idx}.")


        ser.close()

    def change_addr(self):
        if self.tof_idx == 0:
            raise ValueError("0 is placeholder. Use sensor IDs starting at 1.")

        old_addr = c.c_uint16(self.default_addr)
        sensor_id = c.c_uint16(0)

        # Enable power to sensor using Xiao xshut controller

        
        # Check if device is live
        while True:
            status = lib.VL53L4CD_GetSensorId(old_addr, c.byref(sensor_id))

            if status != 0:
                raise RuntimeError(
                    f"GetSensorId failed at 0x29 for xshut{self.tof_idx}:",
                    f"{status}"
                    )
            
            if sensor_id.value == self.expected_sensor_id:
                break

            print(f"No valid VL53L4CD found at 0x29 for xshut{self.tof_idx}")
            time.sleep(0.2)
        
        
        new_linux_addr = addr_pool[self.tof_idx]
        new_st_addr = c.c_uint8(new_linux_addr << 1)

        status = lib.VL53L4CD_SetI2CAddress(old_addr, new_st_addr)
        print("VL53L4CD_SetI2CAddress() status:", status)

        self.addr = c.c_uint16(new_linux_addr)
        

        status = lib.VL53L4CD_GetSensorId(self.addr, c.byref(sensor_id))
        print("VL53L4CD_GetSensorId() status:", status)
        print("New I2C address:", hex(new_linux_addr))
        print(f"sensor_id: 0x{sensor_id.value:04x}")

    def init(self):
        # Initialise sensor
        status = lib.VL53L4CD_SensorInit(self.addr)
        print("SensorInit:", status)

        # Set sensor timing (device, timing_budget_ms, inter_measurement_ms )
        status = lib.VL53L4CD_SetRangeTiming(self.addr,
                                               self.timing_budget_ms,
                                               self.intermeasurement_ms) 
        print("SetRangeTiming:", status)

        # Start ranging on the sensor
        status = lib.VL53L4CD_StartRanging(self.addr)
        print("StartRanging:", status)

        
    def poll_once(self):

        self.ready.value = 0

        # Check for data_ready interrupt flag.
        # Note: byref(ready) is equivalent to &ready in C. Gets address.
        while self.ready.value != 1:
            status = lib.VL53L4CD_CheckForDataReady(self.addr,
                                                    c.byref(self.ready))
            if status != 0:
                raise RuntimeError(f"CheckForDataReady failed: {status}")
            time.sleep(0.002)

        # Get results data from sensor
        status = lib.VL53L4CD_GetResult(self.addr, c.byref(self.results))
        if status != 0:
            raise RuntimeError(f"GetResult failed: {status}")

        # Clear interrupt flag
        status = lib.VL53L4CD_ClearInterrupt(self.addr)
        if status != 0:
            raise RuntimeError(f"ClearInterrupt failed: {status}")
        
        # Print results
        # print(f"distance = {results.distance_mm} mm, "
        #         f"sigma = {results.sigma_mm} mm")

        # Store results
        latest_distance = self.results.distance_mm
        latest_sigma = self.results.sigma_mm
        latest_status = self.results.range_status
        

        print(f"device=0x{self.addr.value:02x}",
            f"distance={latest_distance} mm, "
            f"sigma={latest_sigma} mm, "
            f"status={latest_status}"
        )

        ######################## End of measurement loop #######################
    
