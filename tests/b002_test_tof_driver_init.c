#include <stdio.h>
#include <stdint.h>
#include "../tof_driver/VL53L4CD_api.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t sensor_id = 0;
    
    uint8_t status = VL53L4CD_SensorInit(device); 

    printf("status = %u\n", status);

    return status;
}

/*
To compile:
gcc tests/b002_test_tof_driver_init.c \
tof_driver/platform.c \
tof_driver/VL53L4CD_api.c \
-o tests/b002_test_tof_driver_init \
-lm

// -lm means link to standard math library 'libm'.

To run:
./tests/b002_test_tof_driver_init
*/
