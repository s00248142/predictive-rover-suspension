To force the app to use `libgpiod` for `gpiozero`'s pin factory:
```python
from gpiozero import LED, Device
from gpiozero.pins.native import NativeFactory
Device.pin_factory = NativeFactory()
print(Device.pin_factory)
```
Output (Shows native was used. That's `libgpiod`):
```bash
alan@edukit3:~/source/repos/camjam-3-normal/tests$ python3 gpiozero_pin_factory_set.py 
<gpiozero.pins.native.NativeFactory object at 0xffffac943d00>
```
However, `libgpiod` is only GPIO. It needs additional setup (layers) to support PWM, etc...
Check system:
```bash
cd /sys/class/pwm/ && ls
```
☝️ It will most likely return empty.
Confirm drivers are in place:
```bash
lsmod | grep -i pwm
```
You should see something like:
```bash
pwm_bcm2835            16384  0
```

Check device tree for PWM nodes:
```bash
ls /proc/device-tree/soc 2>/dev/null | grep -i pwm
```
You should see something like:
```bash
pwm@7e20c000
pwm@7e20c800
```

Edit `config.txt`:
```bash
sudoedit /boot/firmware/config.txt
```
Turn off audio to avoid PWM conflict:
```diff
-dtparam=audio=on
+dtparam=audio=off
```
Append this line:
```
# Enable PWM
dtoverlay=pwm,pin=18,func=2
```
After reboot, try again:
```bash
cd /sys/class/pwm/ && ls
```
Should return something like:
```bash
pwmchip0
```
If you want to find what overlays are available:
```bash
ls /boot/firmware/overlays | grep -i pwm
```