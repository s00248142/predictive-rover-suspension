# Predictive Rover Suspension
Final year project. Using TOF and IMU sensors to assess terrain and body pose respectively, to control BLDC motors using FOC controllers and CAN communication for suspension and body control.
## Nvidia SDK Manager
Connect the Jetson Orin Nano to a Windows PC using a Micro-USB cable, not USB-C (The normal carrier board uses USB-C).
Hold the REC button for a few seconds while pluggin in the power cable. Windows should recognise the device.
From Windows, open SDK Manager. It should see the target hardware. 
Don't choose the developer kit. The Seeed BSP will be required instead.
Deselect CUDA X-AI and keep everything else default.
It should start flashing the NVMe that's on the Jetson.
<br>
Choose pre-config next. This sets username and password in advance.
<br>
Windows can give errors about USB being not optimal. Attempt to disable USB suspend mode in power settings, but this can still give errors.
Alternative: Install Linux SDK in 22.04.
Flashing may seem to take a long time, but at about 20% the OS will already be installed and the SDK may give an error regarding the target's IP address. This is related to the OS on the Jetson not having the expected USB-based IP address, but the OS is already installed. Disconnect and plug into a screen, mouse, and keyboard.




## Desktop or Terminal Boot
To choose console mode:
```bash
sudo systemctl set-default multi-user.target
```
(Saves RAM and CPU resources. Quicker boot)
<br><br>
To go back to desktop mode:
```bash
sudo systemctl set-default graphical.target
```
<br><br>





Don't assume the newest version is the most appropriate.
On Jetson Orin Nano the Python version is 3.10.12 (!!! **Do NOT upgrade** !!!)
<br>
[Notes for ROS2 Humble on Ubuntu 22.04](https://ros2-tutorial.readthedocs.io/en/humble/preamble/python/installing_python.html?)
<br>

## Generic Instructions for Python Project with VS Code and GitHub
<details>
<summary>If the destination of the final target machine is generic Linux, ensure PIP and Venv are installed there first. <br>Click to expand.</summary>

```bash
python3 --version
```