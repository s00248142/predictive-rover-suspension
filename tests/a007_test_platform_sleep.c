
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include "../tof_driver/platform.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t reg = 0x010F;
    uint32_t data32 = 0;
    uint16_t data16 = 0;
    
    uint8_t status = VL53L4CD_RdDWord(device, reg, &data32);

    printf("status = %u, 0x%08x\n", status, data32);

    status = VL53L4CD_WaitMs(0, 1500); // Delay between RdDWord and RdWord

    status = VL53L4CD_RdWord(device, 0x010F, &data16);

    printf("0x%04x\n", data16);

    return status;
}

/*
To compile:
gcc tests/007_test_platform_sleep.c \
tof_driver/platform.c -o tests/007_test_platform_sleep

To run:
./tests/007_test_platform_sleep
*/
