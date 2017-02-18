import urllib.request
import threading

class OwnIP:
    def __init__(self):
        # lock is needed because update_ip is run periodically in a thread
        self.data_lock = threading.Lock()
        self.update_ip()

    # Called in a thread
    def update_ip(self):
        print("    IP: updating own ip")
        with self.data_lock:
            try:
                # it isn't quite possible to figure out own public ip, so we ask it from someone else
                ip = urllib.request.urlopen("http://ip.42.pl/raw", timeout = 15).read().decode()
                self.ip = ip
            except Exception as e:
                print("    IP: exception:")
                print("        " + str(type(e)) + ": " + str(e))
            print("    IP: " + self.ip)

    def get_ip(self):
        with self.data_lock:
            return self.ip
