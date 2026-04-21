import subprocess

# subprocess.run(["whoami"], check=True)
subprocess.run(["sudo", "whoami"], check=True)