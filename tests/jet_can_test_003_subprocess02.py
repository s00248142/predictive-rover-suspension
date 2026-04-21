import subprocess
import time

def run_cmd(cmd):
    print("Running:", cmd)
    subprocess.run(cmd, check=True)

gpio_process = None
cangen_process = None

try:
    run_cmd(["sudo", "ip", "link", "set", "can0", "down"])
    run_cmd(["sudo", "ip", "link", "set", "can0", "type", "can", "bitrate", "1000000"])
    run_cmd(["sudo", "ip", "link", "set", "can0", "up"])

    gpio_process = subprocess.Popen(
        ["gpioset", "--mode=signal", "0", "43=0"]
    )

    print("GPIO running...")

    cangen_process = subprocess.Popen(
    ["cangen", "can0", "-g", "1000", "-I", "123", "-L", "8"]
    )
    
    while True:
        time.sleep(1)

finally:
    print("Cleaning up...")

    if gpio_process is not None:
        gpio_process.kill()
        gpio_process.wait()

    if cangen_process is not None:
        cangen_process.kill()
        cangen_process.wait()

    run_cmd(["sudo", "ip", "link", "set", "can0", "down"])