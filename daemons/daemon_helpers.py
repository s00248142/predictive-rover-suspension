'''
********************************************************************************
* File Name: daemon_helpers.py
* Description: 
*   Used internally by xshut and can_enable startup services to be able to send 
*   shell commands in Linux
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 1.0
********************************************************************************
'''

import subprocess # Linux shell commands (standard library)
import can # python-can

# Simplify sending shell commands
def run_cmd(cmd):
    print("Running:", cmd)
    subprocess.run(cmd, check=True)


# CAN bus class with up and down methods
class CanBus:
    def __init__(self, channel=0, bitrate = 1000000):
        self.channel = channel
        self.bitrate = bitrate

    def start(self):
        # Initialise CAN network using can-utils with SocketCAN
        run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "down"])
        run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "type", 
                 "can", "bitrate", f"{self.bitrate}"])
        run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "up"])

        # Use python-can to attach to a running bus
        self.bus = can.interface.Bus(
            channel=f"can{self.channel}",
            interface="socketcan"
        )

        print(f"can{self.channel} started with {self.bitrate} bitrate.")
        
        return self

    def stop(self):
        # Shut down CAN network
        self.bus.shutdown()
        run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "down"])
        print(f"can{self.channel} stopped")