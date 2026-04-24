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

/* Added: Linux headers.*/
#include <stdio.h>
#include <stdint.h> // uint8_t, uint16_t, etc...
#include <fcntl.h> // File open
#include <unistd.h> // Read, write, close
#include <sys/ioctl.h>
#include <linux/i2c-dev.h> // I2C_SLAVE

/* Added: Private file descriptor intended for I2C bus and link to bus as file*/
static int i2c_fd = -1;
static const char *I2C_BUS = "/dev/i2c-1";

/* Added: Helper function to check if the bus is open */
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


uint8_t VL53L4CD_RdDWord(Dev_t dev, uint16_t RegisterAdress, uint32_t *value)
{
	uint8_t status = 255;
	


	return status;
}

uint8_t VL53L4CD_RdWord(Dev_t dev, uint16_t RegisterAdress, uint16_t *value)
{	
	uint8_t status = 255;

	if (ensure_i2c_open() != 0) {
		return status;
	}
	
	int slave_select = ioctl(i2c_fd, I2C_SLAVE, dev); 

	if (slave_select < 0) {
		perror("Slave select failed.");
		return status;
	}

	uint8_t reg[2];

	reg[0] = RegisterAdress >> 8;
	reg[1] = RegisterAdress & 0xFF;

	int bytes_written = write(i2c_fd, reg, 2); 

	if (bytes_written != 2) { 
		perror("Writing register pointer failed.");
		return status;
	}

	uint8_t data[2];
	

	int bytes_read = read(i2c_fd, data, 2);

	if (bytes_read != 2) { 
		perror("Reading from I2C device register failed.");
		return status;
	}

	*value = (data[0] << 8) | data[1];

	status = 0;

	return status;
}

uint8_t VL53L4CD_RdByte(Dev_t dev, uint16_t RegisterAdress, uint8_t *value)
{
	uint8_t status = 255;
	
	/* To be filled by customer. Return 0 if OK */
	/* Warning : For big endian platforms, fields 'RegisterAdress' and 'value' need to be swapped. */
	//#error "This code is empty, please populate the function with valid code for your processor."

	return status;
}

uint8_t VL53L4CD_WrByte(Dev_t dev, uint16_t RegisterAdress, uint8_t value)
{
	uint8_t status = 255;

	/* To be filled by customer. Return 0 if OK */
	/* Warning : For big endian platforms, fields 'RegisterAdress' and 'value' need to be swapped. */
	//#error "This code is empty, please populate the function with valid code for your processor."

	return status;
}

uint8_t VL53L4CD_WrWord(Dev_t dev, uint16_t RegisterAdress, uint16_t value)
{
	uint8_t status = 255;
	
	/* To be filled by customer. Return 0 if OK */
	/* Warning : For big endian platforms, fields 'RegisterAdress' and 'value' need to be swapped. */
	//#error "This code is empty, please populate the function with valid code for your processor."

	return status;
}

uint8_t VL53L4CD_WrDWord(Dev_t dev, uint16_t RegisterAdress, uint32_t value)
{
	uint8_t status = 255;

	/* To be filled by customer. Return 0 if OK */
	/* Warning : For big endian platforms, fields 'RegisterAdress' and 'value' need to be swapped. */
	//#error "This code is empty, please populate the function with valid code for your processor."

	return status;
}

uint8_t VL53L4CD_WaitMs(Dev_t dev, uint32_t TimeMs)
{
	uint8_t status = 255;
	/* To be filled by customer */
	//#error "This code is empty, please populate the function with valid code for your processor."

	return status;
}


