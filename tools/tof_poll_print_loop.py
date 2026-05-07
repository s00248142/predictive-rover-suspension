import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import tof

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

try:

    while True:
        poll_tof_sensors(sensors)

        for i in sensors:
            print(f"device=0x{i.addr.value:02x}",
                f"distance={i.results.distance_mm} mm, "
                f"sigma={i.results.sigma_mm} mm, "
                f"status={i.results.range_status}"
            )

        time.sleep(0.5)

finally:

    tof.xshut_reset() # Set all xshut off for ToF sensors