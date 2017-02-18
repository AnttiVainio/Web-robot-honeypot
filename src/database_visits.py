import struct
import time
import os
import threading
import socket

# Stores every ip as a 4 byte integer back to back in ips.dat
# Stores front page request times as a single byte type and 8 byte double back to back in hits.dat
#  The type is 1 for new visitors, 0 for old
class DatabaseVisits:
    def __init__(self):
        print("    DATABASE: Loading IPs from ips.dat")
        if not os.path.exists("data"):
            os.makedirs("data")
        self.ips = set()
        try:
            with open(os.path.join("data", "ips.dat"), "rb") as file:
                ip = file.read(4)
                while ip:
                    self.ips.add(struct.unpack("!I", ip)[0])
                    ip = file.read(4)
        except IOError: pass
        print("    DATABASE:", len(self.ips), "unique IPs")
        self.reset_new_data()
        # lock is needed because save_data is run periodically in a thread
        self.data_lock = threading.Lock()
        self.changed = False

    def reset_new_data(self):
        self.new_ips = set()
        self.new_times = b''

    def add_visitor(self, ip):
        # convert ip from quad-dotted format to an integer
        ip = struct.unpack("!I", socket.inet_aton(ip))[0]
        with self.data_lock:
            self.changed = True
            if ip not in self.ips:
                self.ips.add(ip)
                self.new_ips.add(ip)
                self.new_times+= b'\x01'
            else: self.new_times+= b'\x00'
            self.new_times+= struct.pack("d", time.time())

    # Called in a thread
    def save_data(self):
        with self.data_lock:
            # only run when there is new data
            if not self.changed: return
            self.changed = False
            # append new data to the files
            print("    DATABASE: Saving IPs to ips.dat")
            with open(os.path.join("data", "ips.dat"), "ab") as file:
                for i in self.new_ips:
                    file.write(struct.pack("!I", i))
            print("    DATABASE: Saving hits to hits.dat")

            with open(os.path.join("data", "hits.dat"), "ab") as file:
                file.write(self.new_times)
            self.reset_new_data()
            print("    DATABASE:", len(self.ips), "unique IPs")
