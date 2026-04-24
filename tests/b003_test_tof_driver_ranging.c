#include <stdio.h>
#include <stdint.h>
#include "../tof_driver/VL53L4CD_api.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t sensor_id = 0;
    uint8_t status = 0;

    status = VL53L4CD_SensorInit(device); 
    if  (status != 0) return status;

    status = VL53L4CD_StartRanging(device);

    printf("Start ranging status = %u\n", status);

    return status;
}

/*
To compile:

gcc tests/b003_test_tof_driver_ranging.c \
tof_driver/platform.c \
tof_driver/VL53L4CD_api.c \
-o tests/b003_test_tof_driver_ranging \
-lm

// -lm means link to standard math library 'libm'.

To run:

./tests/b003_test_tof_driver_ranging

*/
