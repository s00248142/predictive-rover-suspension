import serial
import time

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
# time.sleep(2)

print("startup:")
print(ser.read_all().decode(errors="ignore"))

pause = 0.05
ser.write(b"0\n") # ' b" " ' means a byte string, which is what we need to send over serial.
ser.flush()
time.sleep(pause)

ser.write(b"1\n")
ser.flush()
time.sleep(pause)

ser.write(b"3\n")
ser.flush()
time.sleep(pause)

ser.write(b"7\n")
ser.flush()
time.sleep(pause)

ser.write(b"15\n")
ser.flush()
time.sleep(pause)

print("reply:")
print(ser.read_all().decode(errors="ignore"))

ser.close()