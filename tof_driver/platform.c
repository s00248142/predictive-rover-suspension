/**
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */

/* Modification of code: */
/* Programmer: Alan Ryan */


#include "platform.h"

/**************************** Added: Linux headers ****************************/
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include <fcntl.h> // open()
#include <unistd.h> // read(), write(), close()
#include <sys/ioctl.h>
#include <linux/i2c-dev.h> // I2C_SLAVE
#include <time.h> // nanosleep() and timespec struct.

/* Added: Private file descriptor intended for I2C bus and link to bus as file*/
static int i2c_fd = -1;
static const char *I2C_BUS = "/dev/i2c-1";

/************* Added: Helper function to check if the bus is open *************/
static int ensure_i2c_open(void)
{
    if (i2c_fd >= 0)
    {
        return 0;
    }

    i2c_fd = open("/dev/i2c-1", O_RDWR);

    if (i2c_fd < 0)
    {
        perror("Failed to open I2C bus");
        return -1;
    }

    return 0;
}
/***************************** End of added helper ****************************/


uint8_t VL53L4CD_RdDWord(Dev_t dev, uint16_t RegisterAdress, uint32_t *value)
{
	uint8_t status = 255;

/*********** Added: Body of VL53L4CD_RdDWord to connect with Linux. ************/
	
	/* Open I2C bus and ensure it is open, using helper function. */	
	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	/* Select address of I2C target device. */
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	/* Select register address within I2C target device. */
	/* Register address is 16-bit. Linux pushes individual bytes on I2C. */
	/* Writing opens the door before reading with I2C registers. */
	uint8_t reg[2];
	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;

	int bytes_written = write(i2c_fd, reg, 2); 

	if (bytes_written != 2) { 
		perror("Writing register pointer failed.");
		return status;
	}

	/* Capture four bytes from register and combine into uint32_t. */
	uint8_t data[4];
	int bytes_read = read(i2c_fd, data, 4);

	if (bytes_read != 4) { 
		perror("Reading double-word from I2C device register failed.");
		return status;
	}
	
	*value = ((uint32_t)data[0] << 24) |
         ((uint32_t)data[1] << 16) |
         ((uint32_t)data[2] << 8)  |
         ((uint32_t)data[3]);

	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/
	return status;
}

uint8_t VL53L4CD_RdWord(Dev_t dev, uint16_t RegisterAdress, uint16_t *value)
{	
	uint8_t status = 255;

/*********** Added: Body of VL53L4CD_RdWord to connect with Linux. ************/
	
	/* Open I2C bus and ensure it is open, using helper function. */	
	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	/* Select address of I2C target device. */
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	/* Select register address within I2C target device. */
	/* Register address is 16-bit. Linux pushes individual bytes on I2C. */
	/* Writing opens the door before reading with I2C registers. */
	uint8_t reg[2];
	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;

	int bytes_written = write(i2c_fd, reg, 2); 

	if (bytes_written != 2) { 
		perror("Writing register pointer failed.");
		return status;
	}

	/* Capture two bytes from register. Pass back address of data to caller. */
	uint8_t data[2];
	int bytes_read = read(i2c_fd, data, 2);

	if (bytes_read != 2) { 
		perror("Reading word from I2C device register failed.");
		return status;
	}

	*value = (data[0] << 8) | data[1];

	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/
	return status;
}

uint8_t VL53L4CD_RdByte(Dev_t dev, uint16_t RegisterAdress, uint8_t *value)
{
	uint8_t status = 255;
	
/*********** Added: Body of VL53L4CD_RdByte to connect with Linux. ************/
	
	/* Open I2C bus and ensure it is open, using helper function. */
	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	/* Select address of I2C target device. */
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	/* Select register address within I2C target device. */
	/* Register address is 16-bit. Linux pushes individual bytes on I2C. */
	uint8_t reg[2];
	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;
	int bytes_written = write(i2c_fd, reg, 2); 

	if (bytes_written != 2) { 
		perror("Writing register pointer failed.");
		return status;
	}

	/* Capture byte from register. Pass back address of data to caller. */

	uint8_t data;
	int bytes_read = read(i2c_fd, &data, 1);

	if (bytes_read != 1) { 
		perror("Reading byte from I2C device register failed.");
		return status;
	}

	*value = data;
	
	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/
	return status;
}

uint8_t VL53L4CD_WrByte(Dev_t dev, uint16_t RegisterAdress, uint8_t value)
{
	uint8_t status = 255;

/*********** Added: Body of VL53L4CD_WrByte to connect with Linux. ************/
	
	/* Open I2C bus and ensure it is open, using helper function. */
	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	/* Select address of I2C target device. */
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	/* Select register address within I2C target device. */
	/* Register address is 16-bit. Linux pushes individual bytes on I2C. */
	/* Write byte register using 3rd byte in array (reg[2]). */
	uint8_t reg[3];
	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;
	reg[2] = value;
	int bytes_written = write(i2c_fd, reg, 3); 

	if (bytes_written != 3) { 
		perror("Writing to I2C device register failed.");
		return status;
	}

	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/
	return status;
}

uint8_t VL53L4CD_WrWord(Dev_t dev, uint16_t RegisterAdress, uint16_t value)
{
	uint8_t status = 255;
	
/*********** Added: Body of VL53L4CD_WrWord to connect with Linux. ************/
	
	/* Open I2C bus and ensure it is open, using helper function. */
	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	/* Select address of I2C target device. */
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	/* Select register address within I2C target device. */
	/* Register address is 16-bit. Linux pushes individual bytes on I2C. */
	/* Write word register using 3rd and 4th bytes in array ([2] and [3]). */
	uint8_t reg[4];
	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;
	reg[2] = value >> 8;
	reg[3] = value & 0xFF;
	int bytes_written = write(i2c_fd, reg, 4); 

	if (bytes_written != 4) { 
		perror("Writing to I2C device register failed.");
		return status;
	}

	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/

	return status;
}

uint8_t VL53L4CD_WrDWord(Dev_t dev, uint16_t RegisterAdress, uint32_t value)
{
	uint8_t status = 255;

/*********** Added: Body of VL53L4CD_WrDWord to connect with Linux. ************/
	
	/* Open I2C bus and ensure it is open, using helper function. */
	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	/* Select address of I2C target device. */
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	/* Select register address within I2C target device. */
	/* Register address is 16-bit. Linux pushes individual bytes on I2C. */
	/* Write double-word register using bytes [2] to [5]. */
	uint8_t reg[6];
	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;
	reg[2] = value >> 24;
	reg[3] = value >> 16;
	reg[4] = value >> 8;
	reg[5] = value & 0xFF;
	int bytes_written = write(i2c_fd, reg, 6); 

	if (bytes_written != 6) { 
		perror("Writing double-word to I2C device register failed.");
		return status;
	}

	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/
	return status;
}

uint8_t VL53L4CD_WaitMs(Dev_t dev, uint32_t TimeMs)
{
	uint8_t status = 255;

/*********** Added: Body of VL53L4CD_WaitMS to connect with Linux. ************/
/* Purpose: The ST driver may request Linux to sleep. */

	(void)dev; // Don't use device. Parameter unused on Linux.

	/* Convert TimeMs into timespec format (seconds + nanoseconds) */
	struct timespec delay;
	delay.tv_sec  = TimeMs / 1000; // Seconds, discarding remainder. Can be 0.
	delay.tv_nsec = (TimeMs % 1000) * 1000000; // Remainder converted to ns.

	nanosleep(&delay, NULL);

	/* Return 0 as 'status' if successful. */
	status = 0;
/**************************** End of added section ****************************/

	return status;
}

/******************************** End of file *********************************/

