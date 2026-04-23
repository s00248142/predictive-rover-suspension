# I2C Notes
Describing Linux usage and C implementation with Python.
## Linux
https://wiki.st.com/stm32mpu/wiki/I2C_i2c-tools
```i2c-tools``` is a set of tools for Linux to interact with I2C.
It comes with some primary tools
- ```i2cdetect```
- ```i2cdump```
- ```i2cget```
- ```i2cset```
- ```i2ctransfer```

Detect system buses:
```i2cdetect -l```

Detect devices on a bus:
```i2cdetect -y -r 1```

Read all the registers on a device at once:
```i2cdump -f -y 1 0x29``` where 0x29 is the address of the device.

Read one register (limited to single byte):
```i2cget -f -y 1 0x29 0x00```
*Note: A register can be read-only.*

I2C Transfer:
Devices can require write access before being read from. ```i2ctransfer``` combines both, so it's the most important shell tool for us. It can handle multiple bytes, unlike above.
Example where device at address 0x29 is being queried for the data in its register that's two bytes in size.
```bash
user@jetson:~$ i2ctransfer -f -y 1 w2@0x29 0x01 0x0F r2
0xeb 0xaa
```






