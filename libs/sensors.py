import socket
import time
import threading
import copy

class Sensors():

    def __init__(self):
        hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(hostname)
        self.port = 12000

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSocket.bind((self.local_ip, self.port))

        self.data_lock = threading.Lock()
        self.data = {
            "acc1": {
                "data": [0.001, 0.001, 10],
                "timestamp": time.time(),
            }
        }
        self.alive = True
        self.start()

    def get_address(self):
        return "{}:{}".format(self.local_ip, self.port)

    def get_values(self):
        with self.data_lock:
            data = copy.copy(self.data)
        return data

    def read(self):
        message, address = self.serverSocket.recvfrom(1024)
        cells = str(message).replace("'", "").split(",")
        acc = list(map(float, cells[-3:]))
        with self.data_lock:
            self.data["acc1"] = {
                "data": acc,
                "timestamp": time.time()
            }

    def run(self):
        while self.alive:
            self.read()
            time.sleep(0.001)

    def start(self):
        with self.data_lock:
            self.alive = True
        t = threading.Thread(target=self.run)
        t.start()

    def stop(self):
        with self.data_lock:
            self.alive = False