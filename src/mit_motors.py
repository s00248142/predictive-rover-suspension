'''
********************************************************************************
* File Name: mit_motors.py
* Description: This file has three purposes:
*   1.  Bind functions in the VL53L4CD driver to Python through 'ctypes' and 
*       shared library that was compiled using platform.c
*   2.  Provide functions for polling ToF sensors 
*       and resetting XSHUT shift register, disabling the ToF sensors.
*   3.  Creates a class for creating sensor objects to access their registers
*       and, ultimately, their time-of-flight data, especially distance
*       and sigma.
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 1.0
********************************************************************************
'''

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

# from __future__ import annotations

from dataclasses import dataclass
import math
# from typing import Optional
import time
import can

def clamp(value: float, low: float, high: float) -> float:
    '''
    Clamp: Ensure that motor ojects can't be asked to go beyond the defined 
    range. The values for the clamp are input as 'lower_deg' and 'upper_deg' for
    safety.
    ''' 
    safe_output = max(low, min(high, value))
    
    return safe_output


def float_to_uint(value: float, low: float, high: float, bits: int) -> int:
    '''
    Structure the output for sending MIT-style can messages by making them fit 
    a specific bit size, for example: position is 0xFFFF (16-bit),
    but velocity, Kp, Kd, and torque are 12-bit 0xFFF.
    '''
    value = clamp(value, low, high) # Clamp for physical safety
    span = high - low
    return int((value - low) * ((1 << bits) - 1) / span)



@dataclass
class MITLimits:
    '''
    Dataclass to match the MIT-style packed CAN frame for position, velocity,
    Kd, Kp, and torque using the limits described in the motor datasheets. 
    '''
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
    '''
    Base superclass for all motors that match the MIT-style CAN packed frame, 
    regardless of their individual differences. 
    Subclasses define CAN IDs and any individual differences for each motor 
    including startup/shutdown commands.
    '''
    
    # Use limits from dataclass
    limits = MITLimits()
    
    # Initialise with intended CAN id, direction, 
    def __init__(
        self,
        bus: can.BusABC, # For use with python-can
        motor_id: int, # Use simple integer 1, 2 etc... not 0x001. RMD needs this
        *,
        mit_id: int, # Generate id based on motor-specific requirements
        direction: int = 1, # Change to -1 to flip direction.
        lower_deg: float = -1.0, # Overide with intended degree range
        upper_deg: float = 1.0, # Overide with intended degree range
        max_delta_deg: float = 5.0, # Rely on loop to move continuously
        default_kp: float = 2.0, # Default from testing motors
        default_kd: float = 0.02,  
    ):

        self.bus = bus 
        self.motor_id = motor_id 
        self.mit_id = mit_id
        self.direction = direction
        self.lower_deg = lower_deg
        self.upper_deg = upper_deg
        self.max_delta_deg = max_delta_deg
        self.default_kp = default_kp
        self.default_kd = default_kd
        
        self._zero_rad: float = 0.0 # Map zero from position at turn-on
        self._last_command_deg: float = 0.0 # Used to limit moves by comparing
        self._filtered_target_deg: float = 0.0 # From low-pass filter
        self._enabled: bool = False


    # Directly send defined list as frame
    def _send_mit_special(self, data: list[int]):
        self.bus.send(
            can.Message(
                arbitration_id=self.mit_id,
                data=data,
                is_extended_id=False,
            )
        )

    # Internal method to build an MIT-style CAN frame
    def _pack_mit_frame(
        self,
        *,
        p_des: float, # Position. 0.0 radians should be 0x7fff
        v_des: float, # Velocity. 0.0 rad/s should be 0x7ff
        kp: float,  
        kd: float,
        t_ff: float, # Torque
    ) -> list[int]:
        lim = self.limits
        # Convert to integers of specific bit-size.
        p_int = float_to_uint(p_des, lim.p_min, lim.p_max, 16)
        v_int = float_to_uint(v_des, lim.v_min, lim.v_max, 12)
        kp_int = float_to_uint(kp, lim.kp_min, lim.kp_max, 12)
        kd_int = float_to_uint(kd, lim.kd_min, lim.kd_max, 12)
        t_int = float_to_uint(t_ff, lim.t_min, lim.t_max, 12)

        # Return as list of 8 bytes for sending with python-can and SocketCAN
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

    # Raw desired output using float values
    def _send_mit_raw(
        self,
        *, # Function calls require keyword explicity in parameters. 
        p_des: float, # Position
        v_des: float = 0.0, # Velocity
        kp: float = 0.0,
        kd: float = 0.0,
        t_ff: float = 0.0, # Torque
    ):
        data = self._pack_mit_frame( # Use method to build required MIT frame
            p_des=p_des,
            v_des=v_des,
            kp=kp,
            kd=kd,
            t_ff=t_ff,
        )
        self.bus.send(
            can.Message( # python-can standard method
                arbitration_id=self.mit_id, # e.g. 0x003 for Cube, 0x403 for RMD
                data=data, # List of 8 bytes from _pack_mit_frame return
                is_extended_id=False,
            )
        )

        # Add delay for RMD motor reply
        delay_s = getattr(self, "post_command_delay_s", 0.0)
        if delay_s > 0.0:
            time.sleep(delay_s)



    # Don't use this command directly. Too fast.
    def command_position_deg(
        self,
        target_deg: float,
        *, # Function calls require keyword explicity in parameters for kp, kd. 
        kp: float = None,
        kd: float = None,
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

        # Ensure clamp is used for safe range of motor movement.
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
        fluidity: float = 0.5,
        dt: float = 0.01,
        kp: float = None,
        kd: float = None,
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
        
        # time.sleep(0.005)

        return self.command_position_deg(
            self._filtered_target_deg,
            kp=kp,
            kd=kd,
            limit_delta=True,
        )

    # def centre(self, *, kp: Optional[float] = None, kd: Optional[float] = None) -> float:
    #     """Command software zero, respecting max_delta_deg."""
    #     return self.command_position_deg(0.0, kp=kp, kd=kd)

    def set_software_zero_rad(self, zero_rad: float):
        """Set the MIT-frame position that should be treated as zero."""
        self._zero_rad = clamp(zero_rad, self.limits.p_min, self.limits.p_max)
        self._last_command_deg = 0.0

    # # Send a zero-gain signal to fully relax the motor without shutting down.
    # def emergency_neutral(self) -> None:
    #     """
    #     Send a zero-gain, zero-position MIT frame.

    #     This does not necessarily disable the motor; subclasses should provide shutdown
    #     where supported.
    #     """
    #     self._send_mit_raw(p_des=0.0, v_des=0.0, kp=0.0, kd=0.0, t_ff=0.0)
    #     self._enabled = False

# Myactuator RMD-L5015 Subclass
class RMDL5015(MITMotor):
    """
    MYACTUATOR RMD-L5015 in CAN Motion Mode.

    Proprietary commands:
    - 0x140 + ID for shutdown/brake commands.
    - 0x240 + ID replies.
    MIT mode (Motion mode):
    - 0x400 + ID command.
    - 0x500 + ID reply.
    """
    SHUTDOWN = [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    BRAKE_RELEASE = [0x77, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    BRAKE_LOCK = [0x78, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    MIT_NEUTRAL = [0x7F, 0xFF, 0x7F, 0xF0, 0x00, 0x00, 0x07, 0xFF]
    

    def __init__(
        self,
        bus: can.BusABC,
        motor_id: int = 4,
        post_command_delay_s = 0.003, # Required due to slow RMD CAN response
        **kwargs,
    ):
        super().__init__(
            bus,
            motor_id,
            mit_id=0x400 + motor_id, # MIT-style packed frames to this addr
            **kwargs,
        )
        self.tx_id = 0x140 + motor_id # Normal commands for motor at this addr
        self.rx_id = 0x240 + motor_id # Receive msg from motor from this addr
        self.motion_rx_id = 0x500 + motor_id # MIT mode replies
        self.post_command_delay_s = post_command_delay_s # RMD delay for reply

    # def _send_standard(self, data: list[int]) -> None:
    #     self.bus.send(
    #         can.Message(
    #             arbitration_id=self.tx_id,
    #             data=data,
    #             is_extended_id=False,
    #         )
    #     )
    def _send_special(self, data: list[int]):
        self.bus.send(
            can.Message(
                arbitration_id=self.tx_id,
                data=data,
                is_extended_id=False,
            )
        )

    # Disable output using RMD command 0x8000000000000000.
    def shutdown(self):
        self._send_special(self.SHUTDOWN)
        self._enabled = False
        time.sleep(0.1)
        self._send_special(self.BRAKE_LOCK)

    # Neutral MIT output using MIT command 0x7fff7ff0000007ff.
    def neutral(self):
        self._send_mit_special(self.MIT_NEUTRAL)
        self._enabled = False

    # Release holding brake using RMD command 0x7700000000000000.
    def brake_release(self):
        self._send_special(self.BRAKE_RELEASE)

    def query_zero_feedback_position_rad(self, timeout: float = 0.2) -> float:
        """
        Read one RMD Motion Mode feedback frame and return position in radians.
        Feedback ID is 0x500 + motor_id. The first byte is motor ID, 
        then DATA[1:3] contains the packed 16-bit position value using the same 
        -12.5..+12.5 rad range.
        """
        # Ask for a feedback frame by sending a passive zero-gain MIT frame.
        # self._send_mit_raw(p_des=0.0, v_des=0.0, kp=0.0, kd=0.0, t_ff=0.0)
        self._send_mit_special(self.MIT_NEUTRAL)

        # Block until message is received from motor (time-out of 0.2 seconds).
        start = time.time()
        while time.time() - start < timeout:
            msg = self.bus.recv(timeout=timeout) # Receive msg from python-can
            if msg is None:
                continue # Restart the loop
            if msg.arbitration_id != self.motion_rx_id: # IDs must match
                continue
            if len(msg.data) < 8: # Eight bytes in a list
                continue
            # print(f"Reply from zero-gain command: {msg.data}") # Uncomment to debug
            # input("Press Enter to continue...") # Uncomment to debug
            p_int = (msg.data[1] << 8) | msg.data[2] # Combine two bytes as int
            # print(f"\nRead position from CAN (16-bit int):{p_int}") # DB
            # input("Press Enter to continue...") # Uncomment to debug
            span = self.limits.p_max - self.limits.p_min # -12 to +12 radians
            # print(f"\nspan: {span}") # Uncomment to debug
            # input("Press Enter to continue...") # Uncomment to debug
            non_centre_aligned_pos = p_int * span / ((1 << 16) - 1)
            # print(f"\nNon-centre position: {non_centre_aligned_pos}") # Uncomment to debug
            # input("Press Enter to continue...") # Uncomment to debug
            current_pos = non_centre_aligned_pos + self.limits.p_min
            return current_pos

        raise TimeoutError("No RMD motion feedback frame received")

    # def startup(self, *, use_current_position_as_zero: bool = True) -> None:
    def startup(self):
        """
        Safe startup sequence for RMD.

        If use_current_position_as_zero is True, command 0 deg means the physical
        position the motor was at during startup.
        """
        self.shutdown()
        time.sleep(0.1)

        # if use_current_position_as_zero:
        #     current_rad = self.read_motion_feedback_position_rad()
        #     self.set_software_zero_rad(current_rad)
        # else:
        #     self.set_software_zero_rad(0.0)

        current_rad = self.query_zero_feedback_position_rad()
        # print(f"current position: {current_rad} radians") # Uncomment to debug
        # input("Press Enter to continue...") # Uncomment to debug

        self.set_software_zero_rad(current_rad)

        # Send neutral before releasing brake
        # self.neutral()
        time.sleep(0.1)
        

        # self.arm_at_zero()
        self.brake_release()


class CubeMarsGL60II(MITMotor):
    """
    CubeMars GL60 II MIT-style motor.

    Known working manual sequence:
        cansend can0 001#FFFFFFFFFFFFFFFD
        cansend can0 003#FFFFFFFFFFFFFFFE
        cansend can0 003#FFFFFFFFFFFFFFFC

    For CubeMars:
    - MIT command arbitration ID is the motor ID itself.
    - motor_id=0x03 sends motion commands to 0x003.
    """

    ENTER_MOTOR_MODE = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFC]
    EXIT_MOTOR_MODE  = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFD]
    SET_ZERO         = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFE]

    def __init__(
        self,
        bus: can.BusABC,
        motor_id: int = 0x03,
        post_command_delay_s = 0.003, # Required due to slow RMD CAN response
        **kwargs, # Pass other keyword arguments to base class.
    ):
        super().__init__(
            bus,
            motor_id,
            mit_id=motor_id,
            **kwargs,
        )
        self.post_command_delay_s = post_command_delay_s # RMD delay for reply

    def _send_special(
        self,
        data: list[int]
    ):
        self.bus.send(
            can.Message(
                arbitration_id=self.mit_id,
                data=data,
                is_extended_id=False,
            )
        )

    def enter_motor_mode(self):
        self._send_special(self.ENTER_MOTOR_MODE)

    # def exit_motor_mode(self) -> None:
    #     self._send_special(
    #         self.EXIT_MOTOR_MODE,
    #         arbitration_id=self.reset_id,
    #     )
    #     self._enabled = False
    def exit_motor_mode(self):
        self._send_special(self.EXIT_MOTOR_MODE)
        self._enabled = False

    def set_current_position_zero(self):
        self._send_special(self.SET_ZERO)
        self._zero_rad = 0.0
        self._last_command_deg = 0.0
        self._filtered_target_deg = 0.0

    def startup(
        self,
        *,
        use_current_position_as_zero: bool = False,
        set_zero: bool = True,
    ):
        """
        Startup for CubeMars GL60 II.

        set_zero=True sends the hardware zero command:
            0x003#FFFFFFFFFFFFFFFE

        use_current_position_as_zero is accepted so the same app code can be used
        for RMD and CubeMars, but for CubeMars this class currently does not read
        feedback position before startup. So it behaves as software-zero = 0 rad.

        Typical safe use:
            startup(set_zero=False)

        Known manual zeroing use:
            startup(set_zero=True)
        """

        # Match your known first manual frame:
            # cansend can0 001#FFFFFFFFFFFFFFFD
            # self._send_special(
            #     self.EXIT_MOTOR_MODE,
            #     arbitration_id=self.reset_id,
            # )

        # cansend can0 003#FFFFFFFFFFFFFFFD
        self.exit_motor_mode()
        time.sleep(0.2)
        # if set_zero:

        # cansend can0 003#FFFFFFFFFFFFFFFE
        self.set_current_position_zero()
        time.sleep(0.2)

        # cansend can0 003#FFFFFFFFFFFFFFFC
        self.enter_motor_mode()

        self.set_software_zero_rad(0.0)
        # self.arm_at_zero()

    def shutdown(self):
        self.exit_motor_mode()

################################################################################
# STM32 B-G431B-ESC1 Subclass
################################################################################

class STM32_ESC(MITMotor):
    """
    STM32 B-G431B-ESC1 with 6-step control of GM3506 gimbal motor.

    Proprietary commands:
    - 0x000 + ID for shutdown/brake commands.
    - 0x300 + ID replies.
    No proper MIT mode. No position or torque. 
    First two frames will be substituted with speed control instead of position.
    Frame [0] and [1] are speed with 0x7FFF as zero send and reply
    Frame [2] and [3] are Voltage of supply bus (16-bit ADC) reply only

    """
    SHUTDOWN = [0x7F, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    STM_NEUTRAL = [0x7F, 0xFF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
    

    def __init__(
        self,
        bus: can.BusABC,
        motor_id: int = 5,
        post_command_delay_s = 0.003, # Required due to slow CAN response
        max_rpm = 600, 
        min_rpm = -600,
        limit_rpm_upper = 100,
        limit_rpm_lower = -100,
        **kwargs,
    ):
        super().__init__(
            bus,
            motor_id,
            mit_id=0x000 + motor_id, # MIT-style packed frames to this addr
            **kwargs,
        )
        self.rx_id = 0x300 + motor_id # Receive msg from motor from this addr
        self.post_command_delay_s = post_command_delay_s # Delay for reply
        self.max_rpm = max_rpm
        self.min_rpm = min_rpm
        self.limit_rpm_lower = limit_rpm_lower
        self.limit_rpm_upper = limit_rpm_upper


    def _send_special(self, data: list[int]):
        self.bus.send(
            can.Message(
                arbitration_id=self.mit_id,
                data=data,
                is_extended_id=False,
            )
        )

    
# Internal method to build an MIT-style CAN frame

    def _pack_stm_frame(self, *, speed: float, enable: int) -> list[int]:
        speed = clamp(speed, self.limit_rpm_lower, self.limit_rpm_upper)

        max_rpm = max(abs(self.limit_rpm_lower), abs(self.limit_rpm_upper))
        raw = int(0x7FFF + (speed / max_rpm) * 0x7FFF)
        raw = clamp(raw, 0x0000, 0xFFFF)

        return [
            (raw >> 8) & 0xFF,
            raw & 0xFF,
            enable & 0x01,
            0, 0, 0, 0, 0
        ]

# Raw desired output using float values
    def _send_stm_raw(
        self,
        *, # Function calls require keyword explicity in parameters. 
        speed: float, # Position
        enable: int
    ):
        # Use method to build STM frame
        data = self._pack_stm_frame( 
            speed=speed,
            enable=enable
        )
        self.bus.send(
            can.Message( # python-can standard method
                arbitration_id=self.mit_id, # e.g. 0x003 for Cube, 0x403 for RMD
                data=data, # List of 8 bytes from _pack_mit_frame return
                is_extended_id=False,
            )
        )

        # Add delay for RMD motor reply
        delay_s = getattr(self, "post_command_delay_s", 0.0)
        if delay_s > 0.0:
            time.sleep(delay_s)

    # Disable output using Own command 0x7FFF000000000000.
    def shutdown(self):
        self._send_special(self.SHUTDOWN)
        self._enabled = False
        time.sleep(0.1)

    # Neutral MIT output using MIT command 0x7FFF010000000000.
    def neutral(self):
        self._send_mit_special(self.STM_NEUTRAL)
        self._enabled = False

    def query_zero_feedback_rpm(self, timeout: float = 0.2) -> float:
        """
        Read one STM feedback frame and return speed in RPM.
        Feedback ID is 0x300 + motor_id.
        DATA[0:3] contains the packed 16-bit speed value using 0x7fff as zero.
        """
        # Ask for a feedback frame by sending a passive zero-gain MIT frame.
        # self._send_mit_raw(p_des=0.0, v_des=0.0, kp=0.0, kd=0.0, t_ff=0.0)
        self._send_mit_special(self.STM_NEUTRAL)

        # Block until message is received from motor (time-out of 0.2 seconds).
        start = time.time()
        while time.time() - start < timeout:
            msg = self.bus.recv(timeout=timeout) # Receive msg from python-can
            if msg is None:
                continue # Restart the loop
            if msg.arbitration_id != self.rx_id: # IDs must match
                continue
            if len(msg.data) < 8: # Eight bytes in a list
                continue
            raw = (msg.data[0] << 8) | msg.data[1]
            max_rpm = max(abs(self.limit_rpm_lower), abs(self.limit_rpm_upper))
            current_rpm = ((raw - 0x7FFF) / 0x7FFF) * max_rpm
            return current_rpm

        raise TimeoutError("No STM32 ESC CAN feedback frame received")
    
    def poll_feedback_stm(self):
        msg = self.bus.recv(timeout=0.0)  # non-blocking

        if msg is None or msg.arbitration_id != self.rx_id or len(msg.data) < 8:
            return None

        raw_speed = (msg.data[0] << 8) | msg.data[1]

        # max_rpm needs to match setting within STM main.c ' CAN_MAX_RPM
        rpm = ((raw_speed - 0x7FFF) / 0x7FFF) * self.max_rpm

        # Voltage reading in message is x10. i.e. 203 is 20.3V
        voltage_x10 = (msg.data[2] << 8) | msg.data[3]
        voltage = voltage_x10 / 10.0

        # Duty cycle, direction, and state from 6-step
        duty = (msg.data[4] << 8) | msg.data[5]
        direction = msg.data[6]
        state = msg.data[7]

        return rpm, voltage, duty, direction, state

    # def startup(self, *, use_current_position_as_zero: bool = True) -> None:
    def startup(self):
        """
        Basic function to match prototypes of other motors
        """
        current_rpm = self.query_zero_feedback_rpm() # Neutral with reply
        print(f"{self.mit_id} is alive with {current_rpm} rpm at startup.")
        time.sleep(0.1)

    # Call send_rpm(target_rpm) from to operate the motor.
    def send_rpm(self, target_rpm: float):
        now = time.monotonic()

        target_rpm = clamp(
            target_rpm,
            self.limit_rpm_lower,
            self.limit_rpm_upper
        )

        self._send_stm_raw(speed=target_rpm, enable=0x01)

