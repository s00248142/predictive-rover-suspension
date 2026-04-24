#include <stdio.h>
#include <stdint.h>
#include "../tof_driver/VL53L4CD_api.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t sensor_id = 0;
    
    uint8_t status = VL53L4CD_GetSensorId(device, &sensor_id); 

    printf("status = %u, sensor_id = 0x%04x\n", status, sensor_id);

    return status;
}

/*
To compile:
gcc tests/b001_test_tof_driver.c \
tof_driver/platform.c \
tof_driver/VL53L4CD_api.c \
-o tests/b001_test_tof_driver \
-lm

// -lm means link to standard math library 'libm'.

To run:
./tests/b001_test_tof_driver
*/
