import time

import can # python-can
from mit_motors import RMDL5015, CubeMarsGL60II

# Select CAN bus 'can0' for initiating motor objects
can0 = can.Bus(interface='socketcan', channel='can0')

print("ready")
time.sleep(2)

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
    default_kp=12.0,
    default_kd=0.2,
)

right_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=2,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=1,
    default_kp=12.0,
    default_kd=0.2,
)

rear_motor = CubeMarsGL60II(
    bus=can0,
    motor_id=3,
    lower_deg=-90,
    upper_deg=1,
    max_delta_deg=5,
    direction=1,
    default_kp=6.0,
    default_kd=0.1,
)

left_motor.startup()
time.sleep(0.1)

right_motor.startup()
time.sleep(0.01)

rear_motor.startup()
time.sleep(0.1)

steering_motor.startup()
time.sleep(0.1)

# input("Startup complete. Press Enter to continue...")


dt = 0.01

count = 0
while count < 200:


    # suspension = -70  # e.g. -80 to +80
    # steering = 0
    
    steering_motor.move(0) # RMD motor
    left_motor.move(-70)
    right_motor.move(-70)
    rear_motor.move(-70)
    
    time.sleep(dt)
    count = count + 1

input("Move command sent. Press Enter to continue...")

count = 0
while count < 200:


    # suspension = -70  # e.g. -80 to +80
    # steering = 0
    
    steering_motor.move(-30) # RMD motor
    left_motor.move(-50)
    right_motor.move(-80)
    rear_motor.move(-65)
    
    time.sleep(dt)
    count = count + 1

input("Move command sent. Press Enter to continue...")

count = 0
while count < 200:


    # suspension = -70  # e.g. -80 to +80
    # steering = 0
    
    steering_motor.move(30) # RMD motor
    left_motor.move(-80)
    right_motor.move(-50)
    rear_motor.move(-65)
    
    time.sleep(dt)
    count = count + 1

input("Move command sent. Press Enter to continue...")

count = 0
while count < 200:

    steering_motor.move(0)
    left_motor.move(0)
    right_motor.move(0)
    rear_motor.move(0)

    time.sleep(dt)
    count = count + 1


steering_motor.shutdown()
left_motor.shutdown()
right_motor.shutdown()
rear_motor.shutdown()



