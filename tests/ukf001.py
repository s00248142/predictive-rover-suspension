import numpy as np
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

# Create the filter:
my_filter = KalmanFilter(dim_x=2, dim_z=1)

# Initialise the filter's matrices.

my_filter.x = np.array([[2.],
                [0.]])       # initial state (location and velocity)

my_filter.F = np.array([[1.,1.],
                [0.,1.]])    # state transition matrix

my_filter.H = np.array([[1.,0.]])    # Measurement function
my_filter.P *= 1000.                 # covariance matrix
my_filter.R = 5                      # state uncertainty
my_filter.Q = Q_discrete_white_noise(dim=2, dt=0.1, var=0.1) # process uncertainty

# Main section:
while True:
    my_filter.predict()
    my_filter.update(get_some_measurement())

    # do something with the output
    x = my_filter.x
    do_something_amazing(x)