
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include "../tof_driver/platform.h"

int main(void) {
    
    uint8_t data = 0x21;
    
    uint8_t status = VL53L4CD_WrByte(0x29, 0x0087, data);

    printf("0x%02x\n", data);

    return status;
}

/*
To compile:
gcc tests/003_test_platform_write_byte.c \
tof_driver/platform.c -o tests/003_test_platform_write_byte

To run:
./tests/003_test_platform_write_byte
*/