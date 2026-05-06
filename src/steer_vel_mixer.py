'''
Placeholder for future development.
Intent to mix steering and individual wheel velocities that match physical 
geometry. 
The curve() method from CAMJAM is a good example of a normalising mixer for 
differential steering.
'''

# Convert joystick normalised axis to RPM
def axis_to_rpm(axis, max_rpm):

    return int(axis * max_rpm)