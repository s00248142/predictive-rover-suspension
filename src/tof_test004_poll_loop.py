import tof
import time


def poll_tof_sensors(sensors):
    for sensor in sensors:
        sensor.poll_once()
    

sensors = [
    tof.TofSensor(tof_idx=1),
    tof.TofSensor(tof_idx=2),
    tof.TofSensor(tof_idx=3),
    tof.TofSensor(tof_idx=4),
]

# tof.xshut_reset() # Set all xshut off for ToF sensors

while True:
    poll_tof_sensors(sensors)

    time.sleep(0.5)
