# System Startup

## Can 0 Enable Permanently (holding GPIO line 46 open)
Create service file:
```bash
sudo nano /etc/systemd/system/can0_enable.service
```
Contents:
```bash
# /etc/systemd/system/can0_enable.service
# Takes ownership of GPIO line 46
[Unit]
Description=Enable CAN 0 at startup and own GPIO line 46
After=xshut_startup.service
#Before=rover.service

[Service]
WorkingDirectory=/home/user/code/predictive-rover-suspension/
ExecStart=/home/user/code/predictive-rover-suspension/.venv/bin/python /home/user/code/predictive-rover-suspension/daemons/can0_enable.py
Restart=on-failure
User=user

[Install]
WantedBy=multi-user.target
```
Optionally start now:
```bash
sudo systemctl daemon-reload
```

Enable permanently using terminal:
```bash
sudo systemctl enable can0_enable.service
```
Check status:
```bash
sudo systemctl status can0_enable.service
```
View logs:
```bash
journalctl -u can0_enables.service -f
```

## Xshut reset early:
 
## Systemd service
Create service file:
```bash
sudo nano /etc/systemd/system/xshut_startup.service
```
Contents:
```bash
# /etc/systemd/system/xshut-reset.service
[Unit]
Description=Reset ToF XSHUT shift register
After=dev-spidev0.0.device
#Before=rover.service

[Service]
Type=oneshot
ExecStart=/home/user/code/predictive-rover-suspension/.venv/bin/python /home/user/code/predictive-rover-suspension/daemons/xshut_startup.py

[Install]
WantedBy=multi-user.target
```
Optionally start now:
```bash
sudo systemctl daemon-reload
```

Enable permanently using terminal:
```bash
sudo systemctl enable xshut_startup.service
```
Check status:
```bash
sudo systemctl status xshut_startup.service
```
View logs:
```bash
journalctl -u xshut_startup.service -f
```

## Start ```main.py``` automatically:

Create service file:
```bash
sudo nano /etc/systemd/system/rover.service
```
```bash
# /etc/systemd/system/rover.service
[Unit]
Description=Predictive Rover Suspension App
After=xshut-reset.service # bluetooth.service
Requires=xshut-reset.service

[Service]
WorkingDirectory=/home/user/code/predictive-rover-suspension/src
ExecStart=/home/user/code/predictive-rover-suspension/.venv/bin/python /home/user/code/predictive-rover-suspension/src/main.py
Restart=on-failure
User=user

[Install]
WantedBy=multi-user.target
```
Enable permanently using terminal:
```bash
sudo systemctl enable rover.service
```
Check status:
```bash
sudo systemctl status rover.service
```
Disable automatic start:
```bash
sudo systemctl disable rover.service
```
Disable now:
```bash
sudo systemctl stop rover.service
```
Do both:
```bash
sudo systemctl disable --now rover.service
```
