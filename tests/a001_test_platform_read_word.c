
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
//#include <fcntl.h> // File open
//#include <unistd.h> // Read, write, close
//#include <sys/ioctl.h>
//#include <linux/i2c-dev.h> // I2C_SLAVE
#include "../tof_driver/platform.h"

int main(void) {
    
    uint16_t data = 0;
    
    uint8_t status = VL53L4CD_RdWord(0x29, 0x010F, &data);

    printf("0x%04x\n", data);

    return status;
}


/*
To compile:
gcc tests/001_test_platform_read_word.c \
tof_driver/platform.c -o tests/001_test_platform_read_word

To run:
./tests/001_test_platform_read_word
*/