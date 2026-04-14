Install:
```bash
sudo apt install python3-smbus
```
```bash
pip3 install smbus2 bmi270
```
Then, edit `config.txt` as the BMI270 package suggests 400kHz
[Here](https://pypi.org/project/bmi270/)
```bash
sudoedit /boot/firmware/config.txt
```
```diff
+dtparam=i2c_baudrate=400000
```
