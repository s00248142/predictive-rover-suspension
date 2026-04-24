
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include "../tof_driver/platform.h"

int main(void) {
    
    uint8_t data = 0;
    
    uint8_t status = VL53L4CD_RdByte(0x29, 0x010F, &data);

    printf("0x%02x\n", data);

    return status;
}

/*
To compile:
gcc tests/002_test_platform_read_byte.c \
tof_driver/platform.c -o tests/002_test_platform_read_byte

To run:
./tests/002_test_platform_read_byte
*/