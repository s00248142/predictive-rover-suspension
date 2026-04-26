import serial
import time

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
# time.sleep(2)

print("startup:")
print(ser.read_all().decode(errors="ignore"))

ser.write(b"0\n")
ser.flush()

time.sleep(0.05)


print("reply:")
print(ser.read_all().decode(errors="ignore"))

ser.close()