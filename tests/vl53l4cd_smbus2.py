"""Jetson/Linux-first VL53L4CD driver using smbus2.

Designed for low-latency polling on Linux SBCs like the Jetson Orin Nano.

Notes
-----
- Uses direct Linux I2C access through smbus2, avoiding Blinka/board overhead.
- Register map, initialization values, and timing formulas are based on public
  VL53L4CD drivers and docs from STMicroelectronics and Adafruit.
- Address here is the 7-bit Linux I2C address (default 0x29).

Install
-------
    pip install smbus2

Typical Jetson permissions
--------------------------
    sudo usermod -aG i2c $USER
    # log out and back in
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
import threading
import time
from typing import Optional

from smbus2 import SMBus, i2c_msg

# Registers
_SOFT_RESET = 0x0000
_I2C_SLAVE_DEVICE_ADDRESS = 0x0001
_VHV_CONFIG_TIMEOUT_MACROP_LOOP_BOUND = 0x0008
_GPIO_HV_MUX_CTRL = 0x0030
_GPIO_TIO_HV_STATUS = 0x0031
_SYSTEM_INTERRUPT_CLEAR = 0x0086
_SYSTEM_START = 0x0087
_RESULT_RANGE_STATUS = 0x0089
_RESULT_SPAD_NB = 0x008C
_RESULT_SIGNAL_RATE = 0x008E
_RESULT_AMBIENT_RATE = 0x0090
_RESULT_SIGMA = 0x0092
_RESULT_DISTANCE = 0x0096
_RANGE_CONFIG_A = 0x005E
_RANGE_CONFIG_B = 0x0061
_INTERMEASUREMENT_MS = 0x006C
_RESULT_OSC_CALIBRATE_VAL = 0x00DE
_FIRMWARE_SYSTEM_STATUS = 0x00E5
_IDENTIFICATION_MODEL_ID = 0x010F

DEFAULT_I2C_ADDR = 0x29
EXPECTED_MODEL_ID = 0xEB
EXPECTED_MODULE_TYPE = 0xAA

RANGE_VALID = 0x00
RANGE_WARN_SIGMA_ABOVE = 0x01
RANGE_WARN_SIGMA_BELOW = 0x02
RANGE_ERROR_DISTANCE_BELOW_DETECTION_THRESHOLD = 0x03
RANGE_ERROR_INVALID_PHASE = 0x04
RANGE_ERROR_HW_FAIL = 0x05
RANGE_WARN_NO_WRAP_AROUND_CHECK = 0x06
RANGE_ERROR_WRAPPED_TARGET_PHASE_MISMATCH = 0x07
RANGE_ERROR_PROCESSING_FAIL = 0x08
RANGE_ERROR_CROSSTALK_FAIL = 0x09
RANGE_ERROR_INTERRUPT = 0x0A
RANGE_ERROR_MERGED_TARGET = 0x0B
RANGE_ERROR_SIGNAL_TOO_WEAK = 0x0C
RANGE_ERROR_OTHER = 0xFF

_STATUS_MAP = [
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_HW_FAIL,
    RANGE_WARN_SIGMA_BELOW,
    RANGE_ERROR_INVALID_PHASE,
    RANGE_WARN_SIGMA_ABOVE,
    RANGE_ERROR_WRAPPED_TARGET_PHASE_MISMATCH,
    RANGE_ERROR_DISTANCE_BELOW_DETECTION_THRESHOLD,
    RANGE_VALID,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_CROSSTALK_FAIL,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_INTERRUPT,
    RANGE_WARN_NO_WRAP_AROUND_CHECK,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_OTHER,
    RANGE_ERROR_MERGED_TARGET,
    RANGE_ERROR_SIGNAL_TOO_WEAK,
]

# 0x2D..0x87 initialization sequence from public VL53L4CD drivers.
_INIT_SEQ = bytes([
    0x12, 0x00, 0x00, 0x11, 0x02, 0x00, 0x02, 0x08, 0x00, 0x08, 0x10, 0x01,
    0x01, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x20, 0x0B, 0x00, 0x00, 0x02, 0x14, 0x21, 0x00, 0x00, 0x05, 0x00,
    0x00, 0x00, 0x00, 0xC8, 0x00, 0x00, 0x38, 0xFF, 0x01, 0x00, 0x08, 0x00,
    0x00, 0x01, 0xCC, 0x07, 0x01, 0xF1, 0x05, 0x00, 0xA0, 0x00, 0x80, 0x08,
    0x38, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x89, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x07, 0x05, 0x06, 0x06, 0x00, 0x00, 0x02, 0xC7, 0xFF,
    0x9B, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
])


@dataclass(slots=True)
class VL53L4CDMeasurement:
    timestamp_ns: int
    distance_mm: int
    range_status: int
    sigma_mm: float
    signal_rate_mcps: float
    ambient_rate_mcps: float
    spad_count: int

    @property
    def valid(self) -> bool:
        return self.range_status == RANGE_VALID


class VL53L4CD:
    def __init__(
        self,
        bus: int = 1,
        address: int = DEFAULT_I2C_ADDR,
        *,
        io_timeout_s: float = 0.1,
    ) -> None:
        self.bus_num = bus
        self.address = address
        self.io_timeout_s = io_timeout_s
        self._bus = SMBus(bus)
        self._lock = threading.Lock()
        self._ranging = False

        model_id, module_type = self.model_info()
        if model_id != EXPECTED_MODEL_ID or module_type != EXPECTED_MODULE_TYPE:
            self.close()
            raise RuntimeError(
                f"Wrong sensor ID/type: model=0x{model_id:02X}, module=0x{module_type:02X}"
            )

    def close(self) -> None:
        try:
            self._bus.close()
        except Exception:
            pass

    def __enter__(self) -> "VL53L4CD":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---------- Low-level I2C ----------
    def _write(self, register: int, data: bytes) -> None:
        payload = struct.pack(">H", register) + data
        with self._lock:
            self._bus.i2c_rdwr(i2c_msg.write(self.address, payload))

    def _read(self, register: int, length: int = 1) -> bytes:
        with self._lock:
            write = i2c_msg.write(self.address, struct.pack(">H", register))
            read = i2c_msg.read(self.address, length)
            self._bus.i2c_rdwr(write, read)
            return bytes(read)

    def _write_u8(self, register: int, value: int) -> None:
        self._write(register, bytes((value & 0xFF,)))

    def _write_u16(self, register: int, value: int) -> None:
        self._write(register, struct.pack(">H", value & 0xFFFF))

    def _write_u32(self, register: int, value: int) -> None:
        self._write(register, struct.pack(">I", value & 0xFFFFFFFF))

    def _read_u8(self, register: int) -> int:
        return self._read(register, 1)[0]

    def _read_u16(self, register: int) -> int:
        return struct.unpack(">H", self._read(register, 2))[0]

    def _read_u32(self, register: int) -> int:
        return struct.unpack(">I", self._read(register, 4))[0]

    # ---------- Device control ----------
    def model_info(self) -> tuple[int, int]:
        info = self._read(_IDENTIFICATION_MODEL_ID, 2)
        return info[0], info[1]

    def wait_for_boot(self, timeout_s: float = 1.0) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._read_u8(_FIRMWARE_SYSTEM_STATUS) == 0x03:
                return
            time.sleep(0.001)
        raise TimeoutError("Timed out waiting for VL53L4CD boot")

    def init(self) -> None:
        self.wait_for_boot()
        self._write(0x002D, _INIT_SEQ)
        self._start_vhv()
        self.clear_interrupt()
        self.stop_ranging()
        self._write_u8(_VHV_CONFIG_TIMEOUT_MACROP_LOOP_BOUND, 0x09)
        self._write_u8(0x000B, 0x00)
        self._write(0x0024, b"\x05\x00")
        self.set_inter_measurement_ms(0)
        self.set_timing_budget_ms(50)

    def software_reset(self) -> None:
        self._write_u8(_SOFT_RESET, 0x00)
        time.sleep(0.001)
        self._write_u8(_SOFT_RESET, 0x01)
        time.sleep(0.001)

    def set_address(self, new_address_7bit: int) -> None:
        if not 0x08 <= new_address_7bit <= 0x77:
            raise ValueError("I2C address must be a 7-bit address")
        self._write_u8(_I2C_SLAVE_DEVICE_ADDRESS, new_address_7bit)
        self.address = new_address_7bit

    # ---------- Timing ----------
    def get_inter_measurement_ms(self) -> int:
        reg_val = self._read_u32(_INTERMEASUREMENT_MS)
        clock_pll = self._read_u16(_RESULT_OSC_CALIBRATE_VAL) & 0x03FF
        clock_pll = int(1.065 * clock_pll)
        return 0 if clock_pll == 0 else int(reg_val / clock_pll)

    def set_inter_measurement_ms(self, value_ms: int) -> None:
        if self._ranging:
            raise RuntimeError("Stop ranging before changing inter-measurement period")
        timing_budget = self.get_timing_budget_ms(raw_ok=True)
        if value_ms != 0 and value_ms < timing_budget:
            raise ValueError(
                f"Inter-measurement period cannot be less than timing budget ({timing_budget} ms)"
            )
        clock_pll = self._read_u16(_RESULT_OSC_CALIBRATE_VAL) & 0x03FF
        int_meas = int(1.055 * value_ms * clock_pll)
        self._write_u32(_INTERMEASUREMENT_MS, int_meas)
        self.set_timing_budget_ms(timing_budget)

    def get_timing_budget_ms(self, *, raw_ok: bool = False) -> int:
        osc_freq = self._read_u16(0x0006)
        if osc_freq == 0 and not raw_ok:
            raise RuntimeError("Oscillator frequency is 0")
        if osc_freq == 0:
            return 50

        macro_period_us = 16 * (int(2304 * (1073741824.0 / osc_freq)) >> 6)
        macrop_high = self._read_u16(_RANGE_CONFIG_A)

        ls_byte = (macrop_high & 0x00FF) << 4
        ms_byte = (macrop_high & 0xFF00) >> 8
        ms_byte = 0x04 - (ms_byte - 1) - 1

        timing_budget_ms = (
            ((ls_byte + 1) * (macro_period_us >> 6)) - ((macro_period_us >> 6) >> 1)
        ) >> 12

        if ms_byte < 12:
            timing_budget_ms >>= ms_byte

        if self.get_inter_measurement_ms() == 0:
            timing_budget_ms += 2500
        else:
            timing_budget_ms *= 2
            timing_budget_ms += 4300

        return int(timing_budget_ms / 1000)

    def set_timing_budget_ms(self, value_ms: int) -> None:
        if self._ranging:
            raise RuntimeError("Stop ranging before changing timing budget")
        if not 10 <= value_ms <= 200:
            raise ValueError("Timing budget must be between 10 and 200 ms")

        inter_meas = self.get_inter_measurement_ms()
        if inter_meas != 0 and value_ms > inter_meas:
            raise ValueError(
                f"Timing budget cannot be greater than inter-measurement period ({inter_meas} ms)"
            )

        osc_freq = self._read_u16(0x0006)
        if osc_freq == 0:
            raise RuntimeError("Oscillator frequency is 0")

        timing_budget_us = value_ms * 1000
        macro_period_us = int(2304 * (1073741824.0 / osc_freq)) >> 6

        if inter_meas == 0:
            timing_budget_us -= 2500
        else:
            timing_budget_us -= 4300
            timing_budget_us //= 2

        timing_budget_us <<= 12

        tmp = macro_period_us * 16
        ls_byte = int(((timing_budget_us + ((tmp >> 6) >> 1)) / (tmp >> 6)) - 1)
        ms_byte = 0
        while (ls_byte >> 8) & 0xFFFFFF > 0:
            ls_byte >>= 1
            ms_byte += 1
        encoded = (ms_byte << 8) + (ls_byte & 0xFF)
        self._write_u16(_RANGE_CONFIG_A, encoded)

        tmp = macro_period_us * 12
        ls_byte = int(((timing_budget_us + ((tmp >> 6) >> 1)) / (tmp >> 6)) - 1)
        ms_byte = 0
        while (ls_byte >> 8) & 0xFFFFFF > 0:
            ls_byte >>= 1
            ms_byte += 1
        encoded = (ms_byte << 8) + (ls_byte & 0xFF)
        self._write_u16(_RANGE_CONFIG_B, encoded)

    # ---------- Ranging ----------
    @property
    def interrupt_polarity(self) -> int:
        int_pol = (self._read_u8(_GPIO_HV_MUX_CTRL) & 0x10) >> 4
        return 0 if int_pol else 1

    def data_ready(self) -> bool:
        return (self._read_u8(_GPIO_TIO_HV_STATUS) & 0x01) == self.interrupt_polarity

    def clear_interrupt(self) -> None:
        self._write_u8(_SYSTEM_INTERRUPT_CLEAR, 0x01)

    def start_ranging(self, timeout_s: float = 1.0) -> None:
        mode = 0x21 if self.get_inter_measurement_ms() == 0 else 0x40
        self._write_u8(_SYSTEM_START, mode)
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.data_ready():
                self.clear_interrupt()
                self._ranging = True
                return
            time.sleep(0.001)
        raise TimeoutError("Timed out waiting for first VL53L4CD sample")

    def stop_ranging(self) -> None:
        self._write_u8(_SYSTEM_START, 0x00)
        self._ranging = False

    def _start_vhv(self) -> None:
        self.start_ranging()
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if self.data_ready():
                return
            time.sleep(0.001)
        raise TimeoutError("Timed out starting VHV")

    def range_status(self) -> int:
        status = self._read_u8(_RESULT_RANGE_STATUS) & 0x1F
        return _STATUS_MAP[status] if status < len(_STATUS_MAP) else RANGE_ERROR_OTHER

    def distance_mm(self) -> int:
        return self._read_u16(_RESULT_DISTANCE)

    def sigma_mm(self) -> float:
        return self._read_u16(_RESULT_SIGMA) / 4.0 / 10.0

    def signal_rate_mcps(self) -> float:
        return self._read_u16(_RESULT_SIGNAL_RATE) / 128.0

    def ambient_rate_mcps(self) -> float:
        return self._read_u16(_RESULT_AMBIENT_RATE) / 128.0

    def spad_count(self) -> int:
        return self._read_u16(_RESULT_SPAD_NB) // 256

    def read_measurement(self, *, clear_interrupt: bool = True) -> VL53L4CDMeasurement:
        measurement = VL53L4CDMeasurement(
            timestamp_ns=time.monotonic_ns(),
            distance_mm=self.distance_mm(),
            range_status=self.range_status(),
            sigma_mm=self.sigma_mm(),
            signal_rate_mcps=self.signal_rate_mcps(),
            ambient_rate_mcps=self.ambient_rate_mcps(),
            spad_count=self.spad_count(),
        )
        if clear_interrupt:
            self.clear_interrupt()
        return measurement

    def wait_for_data_ready(self, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.data_ready():
                return True
        return False
