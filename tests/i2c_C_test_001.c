
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include <fcntl.h> // File open
#include <unistd.h> // Read, write, close
#include <sys/ioctl.h>
#include <linux/i2c-dev.h> // I2C_SLAVE

int main(void) {
    
    // open /dev/i2c-1, O_RDWR means open and read for writing.
    int i2c_fd = open("/dev/i2c-1", O_RDWR); // File descriptor handle integer

    if (i2c_fd < 0) {
        perror("Open failed."); // Print error to console
        return 1;
    }


    /* Set target slave address 0x29. Once ioctl() has accessed a device,
    there's no need to use its address for open() or close()... */
    ioctl(i2c_fd, I2C_SLAVE, 0x29); // Talk to this I2C device

    if (ioctl(i2c_fd, I2C_SLAVE, 0x29) < 0) {
        perror("Slave select failed.");
        return 1;
    }

    /* Create array of two bytes for the target register on I2C device. */
    uint8_t reg[2] = {0x01, 0x0F}; // For single-byte buffer on I2C bus.

    /* Write two bytes to gain access to the register being pointed to in 'reg'.
       Data is not writing to the register.
       It's really requesting permission to access. */
    write(i2c_fd, reg, 2); //(file descriptor, pointer_to_buffer, size_of_array)

    
    if (write(i2c_fd, reg, 2) != 2) { // Check bytes written was 2.
        perror("Writing register pointer failed.");
        return 1;
    }
    
    /* After the write() command, the door is open to the 0x010F register.
    Read the two bytes and store the data in the the 'data' variable. */
    uint8_t data[2];
    int bytes_read = read(i2c_fd, data, 2);

    if (bytes_read != 2) { // Check bytes read was 2.
        perror("Reading from I2C device register failed.");
        return 1;
    }

    /* Print the bytes and combine value into 16-bit hex format for viewing */
    printf("0x%02x%02x\n", data[0], data[1]);

    // Close the file.
    close(i2c_fd);

    return 0; // Tell Linux 'Success'.
}