
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include "../tof_driver/platform.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t reg = 0x0064;
    uint16_t data = 0x21;
    
    uint8_t status = VL53L4CD_WrWord(device, reg, data);

    printf("status = %u, 0x%04x\n", status, data);

    return status;
}

/*
To compile:
gcc tests/004_test_platform_write_word.c \
tof_driver/platform.c -o tests/004_test_platform_write_word

To run:
./tests/004_test_platform_write_word
*/