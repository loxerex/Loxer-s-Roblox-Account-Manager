
import time
import sys
from threading import Thread
from rblib import r_client
def enable_roblox_multi_instance():
    r = r_client.hold_singletonMutex()
    if r:
        print("[+] You can now launch multiple Roblox instances.")

if __name__ == "__main__":
    if sys.platform != "win32":
        print("This script only works on Windows.")
    else:
        enable_roblox_multi_instance()
        while True:
            time.sleep(1)
