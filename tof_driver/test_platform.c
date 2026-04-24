
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
//#include <fcntl.h> // File open
//#include <unistd.h> // Read, write, close
//#include <sys/ioctl.h>
//#include <linux/i2c-dev.h> // I2C_SLAVE
#include "platform.h"

int main(void) {
    
    uint16_t id = 0;
    
    uint8_t status = VL53L4CD_RdWord(0x29, 0x010F, &id);

    printf("0x%04x\n", id);

    return status;
}


/*
To compile:
gcc test_platform.c platform.c -o test_platform
*/