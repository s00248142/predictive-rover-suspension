'''
********************************************************************************
* File Name: helpers.py
* Description: Generic helper functions
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 1.0
********************************************************************************
'''

import subprocess # Linux shell commands (standard library)

# Simplify sending shell commands
# Example: run_cmd(["sudo", "ip", "link", "set", f"can{self.channel}", "down"])
def run_cmd(cmd):
    print("Running:", cmd)
    subprocess.run(cmd, check=True)

# Generic clamp function. Can be called using any data type
def clamp(value, low, high):
    return max(low, min(high, value))

# ******************************* End of file **********************************




