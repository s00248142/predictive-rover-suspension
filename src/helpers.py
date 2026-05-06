import subprocess # Linux shell commands (standard library)
import can # python-can

# Simplify sending shell commands
# Example: run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "down"])
def run_cmd(cmd):
    print("Running:", cmd)
    subprocess.run(cmd, check=True)


# Generic clamp function. Can be called using any data type
def clamp(value, low, high):
    return max(low, min(high, value))

'''Below has been moved to daemon_helpers.py'''
# # CAN bus class with up and down methods
# class CanBus:
#     def __init__(self, channel=0, bitrate = 1000000):
#         self.channel = channel
#         self.bitrate = bitrate

#     def start(self):
#         # Initialise CAN network using can-utils with SocketCAN
#         run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "down"])
#         run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "type", 
#                  "can", "bitrate", f"{self.bitrate}"])
#         run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "up"])

#         # Use python-can to attach to a running bus
#         self.bus = can.interface.Bus(
#             channel=f"can{self.channel}",
#             interface="socketcan"
#         )

#         print(f"can{self.channel} started with {self.bitrate} bitrate.")
        
#         return self

#     def stop(self):
#         self.bus.shutdown()
#         run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "down"])
#         print(f"can{self.channel} stopped")





