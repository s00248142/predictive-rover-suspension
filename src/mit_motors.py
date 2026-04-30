"""
mit_motors.py

Small MIT-style CAN motor helpers for position-only steering control.

Design goals:
- Command position only: p_des with v_des=0 and t_ff=0.
- Treat turn-on / first commanded position as software zero.
- Clamp commanded position to a configured sweep range.
- Limit sudden jumps with a max per-command delta.
- Allow motor-specific CAN IDs while sharing MIT frame packing.

Units:
- Public steering command: degrees from software zero.
- Internal MIT command: radians.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

import can


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def float_to_uint(value: float, low: float, high: float, bits: int) -> int:
    """Map a float in [low, high] to an unsigned integer with `bits` bits."""
    value = clamp(value, low, high)
    span = high - low
    return int((value - low) * ((1 << bits) - 1) / span)


@dataclass
class MITLimits:
    p_min: float = -12.5      # rad
    p_max: float = 12.5       # rad
    v_min: float = -45.0      # rad/s
    v_max: float = 45.0       # rad/s
    kp_min: float = 0.0
    kp_max: float = 500.0
    kd_min: float = 0.0
    kd_max: float = 5.0
    t_min: float = -24.0      # Nm
    t_max: float = 24.0       # Nm


class MITMotor:
    
    def move_smooth(self, start_deg, end_deg, duration_s, rate_hz=100, sharpness=0.7):
        """
        Blocking test helper: smoothly move between two angles.

        Useful for bench testing, but your main app should usually call move()
        repeatedly from its own fixed-rate loop instead.
        """
        import time

        dt = 1.0 / rate_hz
        steps = max(1, int(duration_s * rate_hz))

        original_deg = self._last_command_deg
        self._last_command_deg = start_deg

        for i in range(steps + 1):
            t = i / steps
            target = start_deg + (end_deg - start_deg) * t
            self.move(target, fluidity=sharpness, dt=dt)
            time.sleep(dt)

        self._last_command_deg = original_deg


    """
    Base class for MIT-style position control.

    Subclasses define CAN IDs and any motor-specific startup/shutdown commands.
    """

    limits = MITLimits()

    def __init__(
        self,
        bus: can.BusABC,
        motor_id: int,
        *,
        mit_id: int,
        direction: int = 1,
        lower_deg: float = -80.0,
        upper_deg: float = 80.0,
        max_delta_deg: float = 5.0,
        default_kp: float = 2.0,
        default_kd: float = 0.02,
    ):
        if direction not in (-1, 1):
            raise ValueError("direction must be 1 or -1")
        if lower_deg >= upper_deg:
            raise ValueError("lower_deg must be less than upper_deg")
        if max_delta_deg <= 0:
            raise ValueError("max_delta_deg must be positive")

        self.bus = bus
        self.motor_id = motor_id
        self.mit_id = mit_id
        self.direction = direction
        self.lower_deg = lower_deg
        self.upper_deg = upper_deg
        self.max_delta_deg = max_delta_deg
        self.default_kp = default_kp
        self.default_kd = default_kd

        # Software-zero behaviour:
        # Desired user angle 0 deg maps to the motor's turn-on / startup position.
        # For motors that can report MIT feedback, this is set from feedback during startup.
        self._zero_rad: float = 0.0
        self._last_command_deg: float = 0.0
        self._filtered_target_deg: float = 0.0
        self._enabled: bool = False

    def _pack_mit_frame(
        self,
        *,
        p_des: float,
        v_des: float,
        kp: float,
        kd: float,
        t_ff: float,
    ) -> list[int]:
        lim = self.limits

        p_int = float_to_uint(p_des, lim.p_min, lim.p_max, 16)
        v_int = float_to_uint(v_des, lim.v_min, lim.v_max, 12)
        kp_int = float_to_uint(kp, lim.kp_min, lim.kp_max, 12)
        kd_int = float_to_uint(kd, lim.kd_min, lim.kd_max, 12)
        t_int = float_to_uint(t_ff, lim.t_min, lim.t_max, 12)

        return [
            (p_int >> 8) & 0xFF,
            p_int & 0xFF,
            (v_int >> 4) & 0xFF,
            ((v_int & 0xF) << 4) | ((kp_int >> 8) & 0xF),
            kp_int & 0xFF,
            (kd_int >> 4) & 0xFF,
            ((kd_int & 0xF) << 4) | ((t_int >> 8) & 0xF),
            t_int & 0xFF,
        ]

    def _send_mit_raw(
        self,
        *,
        p_des: float,
        v_des: float = 0.0,
        kp: float = 0.0,
        kd: float = 0.0,
        t_ff: float = 0.0,
    ) -> None:
        data = self._pack_mit_frame(
            p_des=p_des,
            v_des=v_des,
            kp=kp,
            kd=kd,
            t_ff=t_ff,
        )
        self.bus.send(
            can.Message(
                arbitration_id=self.mit_id,
                data=data,
                is_extended_id=False,
            )
        )

    def arm_at_zero(self) -> None:
        """
        Send a zero-position hold command.

        Call this at startup before commanding nonzero steering.
        Subclasses may override if a motor needs special enter-mode commands.
        """
        self._last_command_deg = 0.0
        self._enabled = True
        self.command_position_deg(0.0)

    def command_position_deg(
        self,
        target_deg: float,
        *,
        kp: Optional[float] = None,
        kd: Optional[float] = None,
        limit_delta: bool = True,
    ) -> float:
        """
        Immediately command a position relative to software zero.

        Most high-rate apps should call move() instead, because move() adds
        stateful smoothing toward the latest destination.

        Returns the actual clamped/slew-limited command angle in degrees.
        """
        if not self._enabled:
            self._enabled = True

        target_deg = clamp(target_deg, self.lower_deg, self.upper_deg)

        if limit_delta:
            lower_step = self._last_command_deg - self.max_delta_deg
            upper_step = self._last_command_deg + self.max_delta_deg
            target_deg = clamp(target_deg, lower_step, upper_step)

        self._last_command_deg = target_deg
        self._filtered_target_deg = target_deg

        # direction flips user steering direction without changing wiring or signs elsewhere.
        # _zero_rad makes command 0 deg mean "wherever the motor was at startup".
        p_des_rad = self._zero_rad + math.radians(target_deg * self.direction)

        self._send_mit_raw(
            p_des=p_des_rad,
            v_des=0.0,
            kp=self.default_kp if kp is None else kp,
            kd=self.default_kd if kd is None else kd,
            t_ff=0.0,
        )
        return target_deg

    def move(
        self,
        target_deg: float,
        *,
        fluidity: float = 0.7,
        dt: float = 0.01,
        kp: Optional[float] = None,
        kd: Optional[float] = None,
    ) -> float:
        """
        High-rate target-following command.

        Call this once per control-loop tick, e.g. at 100 Hz:
            motor.move(destination_deg, fluidity=0.7, dt=0.01)

        fluidity:
            0.0 = very direct / snappy
            1.0 = very fluid / muddy

        The method internally filters the destination and also respects max_delta_deg.
        Returns the actual command angle sent to the motor.
        """
        target_deg = clamp(target_deg, self.lower_deg, self.upper_deg)
        fluidity = clamp(fluidity, 0.0, 1.0)

        # One-pole target filter. Higher fluidity means slower response.
        # At 100 Hz, these values are intentionally conservative for steering tests.
        min_tau = 0.02   # snappy
        max_tau = 0.45   # muddy/fluid
        tau = min_tau + fluidity * (max_tau - min_tau)
        alpha = dt / (tau + dt)

        self._filtered_target_deg += alpha * (target_deg - self._filtered_target_deg)

        return self.command_position_deg(
            self._filtered_target_deg,
            kp=kp,
            kd=kd,
            limit_delta=True,
        )

    def centre(self, *, kp: Optional[float] = None, kd: Optional[float] = None) -> float:
        """Command software zero, respecting max_delta_deg."""
        return self.command_position_deg(0.0, kp=kp, kd=kd)

    def set_software_zero_rad(self, zero_rad: float) -> None:
        """Set the MIT-frame position that should be treated as steering zero."""
        self._zero_rad = clamp(zero_rad, self.limits.p_min, self.limits.p_max)
        self._last_command_deg = 0.0

    def emergency_neutral(self) -> None:
        """
        Send a zero-gain, zero-position MIT frame.

        This does not necessarily disable the motor; subclasses should provide shutdown
        where supported.
        """
        self._send_mit_raw(p_des=0.0, v_des=0.0, kp=0.0, kd=0.0, t_ff=0.0)
        self._enabled = False


class RMDL5015(MITMotor):
    """
    MYACTUATOR RMD-L5015 in CAN Motion Mode.

    Normal commands:
    - 0x140 + ID for shutdown/brake commands.
    - 0x240 + ID replies.
    Motion mode:
    - 0x400 + ID command.
    - 0x500 + ID reply.
    """

    def __init__(
        self,
        bus: can.BusABC,
        motor_id: int = 4,
        **kwargs,
    ):
        super().__init__(
            bus,
            motor_id,
            mit_id=0x400 + motor_id,
            **kwargs,
        )
        self.tx_id = 0x140 + motor_id
        self.rx_id = 0x240 + motor_id
        self.motion_rx_id = 0x500 + motor_id

    def _send_standard(self, data: list[int]) -> None:
        self.bus.send(
            can.Message(
                arbitration_id=self.tx_id,
                data=data,
                is_extended_id=False,
            )
        )

    def shutdown(self) -> None:
        """Disable output using RMD command 0x80."""
        self._send_standard([0x80, 0, 0, 0, 0, 0, 0, 0])
        self._enabled = False

    def brake_release(self) -> None:
        """Release holding brake using RMD command 0x77."""
        self._send_standard([0x77, 0, 0, 0, 0, 0, 0, 0])

    def read_motion_feedback_position_rad(self, timeout: float = 0.2) -> float:
        """
        Read one RMD Motion Mode feedback frame and return position in radians.

        Feedback ID is 0x500 + motor_id. The first byte is motor ID, then DATA[1:3]
        contains the packed 16-bit position value using the same -12.5..+12.5 rad range.
        """
        # Ask for a feedback frame by sending a passive zero-gain MIT frame.
        self._send_mit_raw(p_des=0.0, v_des=0.0, kp=0.0, kd=0.0, t_ff=0.0)

        import time
        start = time.time()
        while time.time() - start < timeout:
            msg = self.bus.recv(timeout=timeout)
            if msg is None:
                continue
            if msg.arbitration_id != self.motion_rx_id:
                continue
            if len(msg.data) < 3:
                continue

            p_int = (msg.data[1] << 8) | msg.data[2]
            span = self.limits.p_max - self.limits.p_min
            return (p_int * span / ((1 << 16) - 1)) + self.limits.p_min

        raise TimeoutError("No RMD motion feedback frame received")

    def startup(self, *, use_current_position_as_zero: bool = True) -> None:
        """
        Safe startup sequence for RMD.

        If use_current_position_as_zero is True, command 0 deg means the physical
        position the motor was at during startup.
        """
        self.shutdown()

        if use_current_position_as_zero:
            current_rad = self.read_motion_feedback_position_rad()
            self.set_software_zero_rad(current_rad)
        else:
            self.set_software_zero_rad(0.0)

        self.arm_at_zero()
        self.brake_release()


class CubeMarsGL60II(MITMotor):
    """
    CubeMars GL60 II MIT-style motor.

    Assumption based on common CubeMars MIT-style operation:
    - Motion command arbitration ID is the motor ID itself.
    - Optional special frames exist for enter/exit/zero depending on firmware.

    Adjust command IDs/special frames if your GL60 II firmware manual differs.
    """

    ENTER_MOTOR_MODE = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFC]
    EXIT_MOTOR_MODE = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFD]
    SET_ZERO = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFE]

    def __init__(
        self,
        bus: can.BusABC,
        motor_id: int,
        **kwargs,
    ):
        super().__init__(
            bus,
            motor_id,
            mit_id=motor_id,
            **kwargs,
        )

    def _send_special(self, data: list[int]) -> None:
        self.bus.send(
            can.Message(
                arbitration_id=self.mit_id,
                data=data,
                is_extended_id=False,
            )
        )

    def enter_motor_mode(self) -> None:
        self._send_special(self.ENTER_MOTOR_MODE)

    def exit_motor_mode(self) -> None:
        self._send_special(self.EXIT_MOTOR_MODE)
        self._enabled = False

    def set_current_position_zero(self) -> None:
        self._send_special(self.SET_ZERO)
        self._last_command_deg = 0.0

    def startup(self, *, set_zero: bool = False) -> None:
        """
        Enter MIT mode and optionally set current position as zero.

        For final steering use, only call set_zero when the mechanism is physically
        centred and you intentionally want to redefine zero.
        """
        self.enter_motor_mode()
        if set_zero:
            self.set_current_position_zero()
        self.arm_at_zero()

    def shutdown(self) -> None:
        self.exit_motor_mode()
