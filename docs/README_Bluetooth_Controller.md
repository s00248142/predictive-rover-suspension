# linux-bluetooth-controllers
Bluetooth setup for controllers in Ubuntu and Home Assistant

<details>
<summary>Odd and ends</summary>

Stop Bluetooth until restart.
```bash
sudo rfkill block bluetooth
```
To unblock:
```bash
sudo rfkill unblock bluetooth
```
</details>

## PS3 Controller
The PS3 controller is a bit odd.
It can't pair directly like newer Bluetooth devices.
It needs to be connected by USB first, then press the 'PS' button, then search for Bluetooth device on the OS. It uses the Bluetooth Classic HID profile.
For USB function, even after Bluetooth pairing has been established, you need to press the 'PS' button after physically plugging in to the computer's USB port **every time**. It will then prioritise USB connection over Bluetooth.

To see the controller connected as a USB device:
```bash
lsusb
```
You should see something like:
```bash
Bus 001 Device 002: ID 054c:0268 Sony Corp. Batoh Device / PlayStation 3 Controller
```
Observe live logs when plugging in and out:
```bash
sudo dmesg -w
```
Example response:
```bash
[ 5302.015083] Indeed it is in host mode hprt0 = 00021501
[ 5302.195042] usb 1-1: new full-speed USB device number 3 using dwc_otg
[ 5302.206574] Indeed it is in host mode hprt0 = 00021501
[ 5302.412278] usb 1-1: New USB device found, idVendor=054c, idProduct=0268, bcdDevice= 1.00
[ 5302.412317] usb 1-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
[ 5302.412332] usb 1-1: Product: PLAYSTATION(R)3 Controller
[ 5302.412346] usb 1-1: Manufacturer: Sony
[ 5302.452192] input: Sony PLAYSTATION(R)3 Controller Motion Sensors as /devices/platform/soc/3f980000.usb/usb1/1-1/1-1:1.0/0003:054C:0268.0002/input/input5
[ 5302.507396] input: Sony PLAYSTATION(R)3 Controller as /devices/platform/soc/3f980000.usb/usb1/1-1/1-1:1.0/0003:054C:0268.0002/input/input4
[ 5302.508239] sony 0003:054C:0268.0002: input,hiddev96,hidraw0: USB HID v81.11 Joystick [Sony PLAYSTATION(R)3 Controller] on usb-3f980000.usb-1/input0
[ 5314.539139] usb 1-1: USB disconnect, device number 3
```
See the controller gets recognised as a joystick:
```bash
ls /dev/input/js*
```
Response:
```bash
/dev/input/js0
```
Get `joystick` package:
```bash
sudo apt list --installed | grep -i joystick
```
If it's not installed:
```bash
sudo apt update
```
```bash
sudo apt install joystick
```
Run `jtest` (part of `joystick` package):
```bash
jstest /dev/input/js0
```
You should see a live response (still USB):
(also, remember the 'PS' should've been pressed to activate the connection)
```
Axes:  0:     0  1:     0  2:-32767  3:-15202  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:-12837  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3: -9121  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3: -5743  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:  -676  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:     0  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:     0  4:     0  5:-32767 Buttons:  0:on   1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:     0  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:     0  4:     0  5:-32767 Buttons:  0:on   1:off  2:off  
3:offAxes:  0:     0  1:     0  2:-32767  3:     0  4:     0  5:-32767 Buttons:  0:off  1:off  2:off  
3:off
```
### Now for the PS3 Bluetooth connection:
PS3 controllers are odd (based on 2006 hardware).<br>
You'll need to use 'Sixpair'.
See if `bluez` is installed:
```bash
apt list --installed | grep bluez
```
```bash
sudo apt update
```
Dependency for 'Sixpair':
```bash
sudo apt install libusb-dev
```


```bash
mkdir ~/sixpair && cd ~/sixpair
```
Then, in that folder get the C file:
```bash
wget https://raw.githubusercontent.com/RetroPie/sixad/master/sixpair.c
```
Compile 'Sixpair':
```bash
gcc -o sixpair sixpair.c -lusb
```
Connect the PS3 controller via USB and press the 'PS' button to get connected.<br>
Then run 'Sixpair':
```bash
sudo ./sixpair
```

Response:
```bash
Current Bluetooth master: d8:3a:dd:12:cc:81
Setting master bd_addr to d8:3a:dd:12:cc:81
```
☝️The MAC address of the Bluetooth controller of the Linux machine gets written into the PS£ controller as its new 'master'.<br><br>
If the controller won't establish a bluetooth connection after that, then it may be a modern security block.<br>
Change the following file:
```bash
sudo nano /etc/bluetooth/input.conf
```
```diff
- #ClassicBondedOnly=True
+ ClassicBondedOnly=false
```
```bash
systemctl restart bluetooth
```
Note: The actual address of the current PS3 controller is E0:AE:5E:9E:66:22

`jstest /dev/input/js0` should work just as before.

## Other
If installed, then the general gist is to discover the desired MAC address, then pair, trust, and connect in quick succession.
```bash
bluetoothctl
```
```bash
power on
```
```bash
agent on
```
```bash
default-agent
```
```bash
discoverable on
```
```bash
pairable on
```
```bash
scan on
```
```bash
pair D8:3A:DD:12:CC:81 
```
```bash
trust D8:3A:DD:12:CC:81 
```
```bash
connect D8:3A:DD:12:CC:81 
```
