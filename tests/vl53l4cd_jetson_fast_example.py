"""Low-latency VL53L4CD example for Jetson Orin Nano.

Wiring on the Jetson 40-pin header:
- Pin 1  -> 3.3V
- Pin 3  -> SDA
- Pin 5  -> SCL
- Pin 6  -> GND

Before running:
    sudo apt update
    sudo apt install -y python3-pip i2c-tools
    pip install smbus2
    sudo usermod -aG i2c $USER
    # log out and back in

Check the sensor is visible first:
    i2cdetect -y 1
    # look for 29
"""

from __future__ import annotations

import time
from statistics import mean

from vl53l4cd_smbus2 import VL53L4CD, RANGE_VALID

BUS = 1
ADDRESS = 0x29
TIMING_BUDGET_MS = 10      # lowest supported by this driver path
INTER_MEASUREMENT_MS = 0   # 0 = continuous mode for lowest latency
PRINT_EVERY_N = 20


def main() -> None:
    samples = []
    last_print = time.monotonic()

    with VL53L4CD(bus=BUS, address=ADDRESS) as tof:
        tof.init()
        tof.stop_ranging()
        tof.set_inter_measurement_ms(INTER_MEASUREMENT_MS)
        tof.set_timing_budget_ms(TIMING_BUDGET_MS)
        tof.start_ranging()

        print("Started VL53L4CD")
        print(f"bus={BUS} address=0x{ADDRESS:02X} timing_budget={TIMING_BUDGET_MS}ms inter_measurement={INTER_MEASUREMENT_MS}ms")

        while True:
            if not tof.wait_for_data_ready(timeout_s=0.050):
                print("Timeout waiting for data")
                continue

            m = tof.read_measurement(clear_interrupt=True)
            samples.append(m)

            if len(samples) >= PRINT_EVERY_N:
                now = time.monotonic()
                dt = now - last_print
                rate_hz = len(samples) / dt if dt > 0 else 0.0
                valid = [s.distance_mm for s in samples if s.range_status == RANGE_VALID]
                latest = samples[-1]
                valid_mean = mean(valid) if valid else float('nan')
                print(
                    f"latest={latest.distance_mm:4d} mm "
                    f"status={latest.range_status:02d} "
                    f"sigma={latest.sigma_mm:5.2f} mm "
                    f"signal={latest.signal_rate_mcps:6.2f} Mcps "
                    f"valid_mean={valid_mean:7.2f} mm "
                    f"loop_rate={rate_hz:6.1f} Hz"
                )
                samples.clear()
                last_print = now


if __name__ == "__main__":
    main()
