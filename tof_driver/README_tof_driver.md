The ```platform.c``` needed to be written for this project to operate the driver from Linux. 

Link to driver:
https://www.st.com/en/embedded-software/stsw-img026.html?ecmp=tt9470_gl_link_feb2019&rt=db&id=DB4579

VL53L4CD ULD user manual UM2931 is available on below link:
https://www.st.com/resource/en/user_manual/um2931-a-guide-to-using-the-vl53l4cd-ultra-lite-driver-uld-stmicroelectronics.pdf 

Datasheet:
https://www.st.com/resource/en/datasheet/vl53l4cd.pdf

ST Wiki on I2C in Linux:
https://wiki.st.com/stm32mpu/wiki/I2C_i2c-tools


The output from the compiled using:
```bash
gcc -shared -fPIC tof_driver/platform.c tof_driver/VL53L4CD_api.c -o tof_driver/libvl53l4cd.so -lm
```
'-lm' links the math library.

How to compile shared objects (.so)
https://www.youtube.com/watch?v=_VtnqLzakDI