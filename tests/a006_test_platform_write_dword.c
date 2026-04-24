
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include "../tof_driver/platform.h"

int main(void) {
    
    Dev_t device = 0x29; // Dev_t is a typedef from platform.h
    uint16_t reg = 0x1234;
    uint32_t data = 0xAABBCCDD;
    
    uint8_t status = VL53L4CD_WrDWord(device, reg, data);

    printf("status = %u, 0x%08x\n", status, data);

    return status;
}

/*
To compile:
gcc tests/006_test_platform_write_dword.c \
tof_driver/platform.c -o tests/006_test_platform_write_dword

To run:
./tests/006_test_platform_write_dword
*/