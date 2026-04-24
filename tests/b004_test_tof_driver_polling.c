#include <stdio.h>
#include <stdint.h>
#include "../tof_driver/VL53L4CD_api.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t sensor_id = 0;
    uint8_t status = 0;
    uint8_t ready = 0;
    VL53L4CD_ResultsData_t results;

    status = VL53L4CD_SensorInit(device); 
    if  (status != 0) return status;

    status = VL53L4CD_StartRanging(device);

    printf("Start ranging status = %u\n", status);

    while(!ready) {
        status = VL53L4CD_CheckForDataReady(device, &ready);
        if (status != 0) return status;

        VL53L4CD_WaitMs(device, 5);
    }

    printf("Data ready\n");

    status = VL53L4CD_GetResult(device, &results);
    if (status != 0) return status;

    printf("Distance = %u mm\n", results.distance_mm);

    status = VL53L4CD_ClearInterrupt(device);
    if (status != 0) return status;

    return status;

}

/*
To compile:

gcc tests/b004_test_tof_driver_polling.c \
tof_driver/platform.c \
tof_driver/VL53L4CD_api.c \
-o tests/b004_test_tof_driver_polling \
-lm

// -lm means link to standard math library 'libm'.

To run:

./tests/b004_test_tof_driver_polling

*/
