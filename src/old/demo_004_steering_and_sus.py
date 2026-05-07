import time
# from helpers import *
# import tof
import can # python-can
from mit_motors import RMDL5015, CubeMarsGL60II




# Initialise I2C for display to indicate program start (blink bottom bar x 2)

# Initialise GPIO for can0 and can1
# gpio_request = None # For gpiod as object showing ownership of pin (GPIO line)
# gpio_request = gpiod.request_lines(
#     "/dev/gpiochip0",
#     config={
#         43: gpiod.LineSettings(
#             direction=gpiod.line.Direction.OUTPUT,
#             output_value=gpiod.line.Value.INACTIVE
#         ),
#         106: gpiod.LineSettings(
#             direction=gpiod.line.Direction.OUTPUT,
#             output_value=gpiod.line.Value.INACTIVE
#         ),
#     },
#     consumer="rover_app_can" # visible to Linux GPIO queries.
# )

# print("GPIO lines 43 & 106 held low. can0 & can1 enabled.")

# # Initialise can0 bus for suspension motors
# can0 = CanBus(channel=0, bitrate=1000000)
# can0.start()


# Select CAN bus 'can0' for initiating motor objects
can0 = can.Bus(interface='socketcan', channel='can0')

print("ready")
time.sleep(3)


steering_motor = RMDL5015(
    bus=can0,
    motor_id=4,
    lower_deg=-80,
    upper_deg=80,
    max_delta_deg=5,
    direction=1,
    default_kp=6,
    default_kd=0.1,
)

left_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=1,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=-1,
    default_kp=8.0,
    default_kd=0.2,
)

right_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=2,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=1,
    default_kp=8.0,
    default_kd=0.2,
)

rear_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=3,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=1,
    default_kp=4.0,
    default_kd=0.1,
)

# steering_motor.startup(use_current_position_as_zero=True)
# time.sleep(0.5)

# left_motor.startup(use_current_position_as_zero=True)
# right_motor.startup(use_current_position_as_zero=True)
# rear_motor.startup(use_current_position_as_zero=True)



# input("Press Enter to continue...")

# left_motor.startup(set_zero=True)
# time.sleep(0.1)

# right_motor.startup(set_zero=True)
# time.sleep(0.1)

# rear_motor.startup(set_zero=True)
# time.sleep(0.1)

left_motor.startup()
time.sleep(0.05)

right_motor.startup()
time.sleep(0.05)

rear_motor.startup()
time.sleep(0.05)

steering_motor.startup()
time.sleep(0.05)

# input("Startup complete. Press Enter to continue...")


dt = 0.01

count = 0
while count < 300:


    suspension = -70  # e.g. -80 to +80
    steering = 0

    # rear_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )

   
    # input("First command in loop sent. Press Enter to continue...")  # Debug

    # steering_motor.move(
    #     steering,
    #     fluidity=0.9,
    #     dt=dt
    # )

    # left_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )

    # right_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )
    
    # rear_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )
    
    steering_motor.move(0) # RMD motor
    # time.sleep(0.005)
    left_motor.move(0)
    right_motor.move(0)
    rear_motor.move(0)
    



    # time.sleep(5)

    # destination = 0

    # rear_motor.move(
    #     destination,
    #     fluidity=0.8,
    #     dt=dt
    # )


    # time.sleep(5)

    time.sleep(dt)
    count = count + 1

input("Move command sent. Press Enter to continue...")

count = 0
while count < 300:
    suspension = 0
      # e.g. -80 to +80
    steering = 0

    # steering_motor.move(
    #     steering,
    #     fluidity=0.9,
    #     dt=dt
    # )

    # left_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )

    # right_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )
    
    # rear_motor.move(
    #     suspension,
    #     fluidity=1,
    #     dt=dt
    # )

    steering_motor.move(0)
    left_motor.move(0)
    right_motor.move(0)
    rear_motor.move(0)

    # time.sleep(5)

    # destination = 0

    # rear_motor.move(
    #     destination,
    #     fluidity=0.8,
    #     dt=dt
    # )


    # time.sleep(5)

    time.sleep(dt)
    count = count + 1

# destination = 0  # e.g. -80 to +80

# steering_motor.move(
#     destination,
#     fluidity=0.9,
#     dt=dt
# )

steering_motor.shutdown()
left_motor.shutdown()
right_motor.shutdown()
rear_motor.shutdown()

# can0.stop()

