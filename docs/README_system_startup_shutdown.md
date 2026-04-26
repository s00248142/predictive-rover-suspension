# System Startup

## Xshut reset early:
 
## Systemd service
Create service file:
```bash
sudo nano /etc/systemd/system/xshut_startup.service
```
```bash
# /etc/systemd/system/xshut-reset.service
[Unit]
Description=Reset ToF XSHUT shift register
After=dev-spidev0.0.device
#Before=rover.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/user/code/predictive-rover-suspension/tools/xshut_startup.py

[Install]
WantedBy=multi-user.target
```
Optionally start now:
```bash
sudo systemctl daemon-reload
```

Enable permanently using terminal:
```bash
sudo systemctl enable xshut-reset.service
```
Check status:
```bash
sudo systemctl status xshut-reset.service
```
View logs:
```bash
journalctl -u rover.service -f
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
ExecStart=/usr/bin/python3 /home/user/code/predictive-rover-suspension/src/main.py
Restart=on-failure
User=user

[Install]
WantedBy=multi-user.target
```
Enable permanently using terminal:
```bash
sudo systemctl enable rover.service
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
