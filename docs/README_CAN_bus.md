# CAN Bus Notes

## Linux
Show current state:
```bash
ip -details link show can0
```
Sequence to get the CAN bus running:
```bash
sudo ip link set can0 down
```
```bash
sudo ip link set can0 type can bitrate 1000000
```
```bash
sudo ip link set can0 up
```


candump can0
Run in a separate terminal window to monitor CAN network:
```bash
candump -tz can0
```

## GL60 II from Linux

Turn on motor
```bash
cansend can0 003#FFFFFFFFFFFFFFFC
```

Turn off motor
```bash
cansend can0 003#FFFFFFFFFFFFFFFD
```

cansend can0 003#8000800001002000
cansend can0 003#8FFF800001002000
