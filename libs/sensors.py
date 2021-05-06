import socket
import time
import threading
import copy
import math

class Sensors():

    def __init__(self, logging=False):
        hostname = socket.gethostname()
        self.IS_LOGGING = logging
        self.local_ip = socket.gethostbyname(hostname)
        self.port = 12000

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSocket.bind((self.local_ip, self.port))

        self.data_lock = threading.Lock()
        self.data = {
            "acc1": {
                "address": False,
                "timestamp": -1,
                "data": False,
                "sampling": [],
            }
        }
        self.data_public = {
        }
        self.alive = True

        if self.IS_LOGGING:
            with open("data.csv", "w") as log:
                log.write("{},{},{}\n".format("a1", "a2", "a3"))

        self.start()



    def get_address(self):
        return "{}:{}".format(self.local_ip, self.port)

    def get_values(self):
        with self.data_lock:
            data = copy.copy(self.data_public)
        for name in data.keys():
            if "timestamp" in data[name]:
                data[name]["online"] = True if time.time() - data[name]["timestamp"] < 0.2 else False
            else:
                data[name]["online"] = False
        return data

    def calc_angles(self, acc):
        roll, pitch, yaw = acc
        roll_yaw_abs = abs(complex(roll, yaw))
        angle = math.atan2(-pitch, roll_yaw_abs)
        angle_roll = math.atan2(pitch, roll)
        angle_yaw = math.atan2(pitch, yaw)

        print(angle_roll, angle_yaw)

        if self.IS_LOGGING:
            with open("data.csv", "a") as log:
                log.write("{},{},{}\n".format(angle, angle_roll, angle_yaw))

    def read(self):
        message, address = self.serverSocket.recvfrom(1024)
        cells = str(message).replace("'", "").split(",")
        acc = list(map(float, cells[-3:]))
        remote_ip = address[0]
        name = "acc1"
        sampling = copy.copy(self.data[name]["sampling"])
        last_timestamp = copy.copy(self.data[name]["timestamp"])

        current_timestamp = time.time()
        sampling.append(current_timestamp - last_timestamp)
        if len(sampling) > 5:
            del sampling[0]
        freq = round(1 / (sum(sampling) / len(sampling)), 2)

        self.calc_angles(acc)

        print(freq)

        self.data[name] = {
            "address": remote_ip,
            "data": acc,
            "timestamp": current_timestamp,
            "sampling": sampling,
            "freq": freq,
        }
        TO_COPY = ("address", "data", "timestamp")
        with self.data_lock:
            for name, values in self.data.items():
                self.data_public[name] = {k: values[k] for k in TO_COPY}

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


if __name__ == "__main__":
    sensors = Sensors(logging=True)

    while True:
        time.sleep(1)
        print(sensors.get_values())