# Masp Based on website below, but many were wrong:
# https://www.pygame.org/docs/ref/joystick.html for PS5 controller
# Use pygame_test_inputs.py in /tools/ for real relationships

# Analogue axes
AXIS_L_X = 0 # left/right
AXIS_L_Y = 1 # up/down
AXIS_R_X = 2 # left/right
AXIS_L2 = 3 # Analogue left trigger
AXIS_R2 = 4 # Analogue right trigger
AXIS_R_Y = 5 # up/down

# Buttons
BTN_SQUARE = 0
BTN_CROSS = 1
BTN_CIRCLE = 2
BTN_TRIANGLE = 3
BTN_L1 = 4
BTN_R1 = 5
BTN_L2 = 6
BTN_R2 = 7
BTN_CREATE = 8
BTN_OPTIONS = 9
BTN_LEFT_STICK = 10
BTN_RIGHT_STICK = 11
BTN_PS = 12

# Direction pad
HAT_DPAD = 0

# Normalise the right, left trigger values from PS5 controller -1 to +1 as-is 
def norm_trigger(val):
    return (val + 1.0) / 2.0

def triggers_to_axis(fwd_raw, rev_raw):
    fwd = norm_trigger(fwd_raw)
    rev = norm_trigger(rev_raw)
    axis = fwd - rev
    return axis



