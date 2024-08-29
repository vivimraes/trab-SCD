import socket
import time

class Process:
    def __init__(self, process_id, coordinator_host='127.0.0.1', coordinator_port=5000, F=10, r=5, k=2):
        self.process_id = process_id
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.F = F
        self.r = r
        self.k = k

    def start(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.coordinator_host, self.coordinator_port))
                s.send(f"{self.process_id}|{'0'*(self.F-len(self.process_id)-1)}".encode())
                for _ in range(self.r):
                    self.send_request(s)
                    self.wait_for_grant(s)
                    self.enter_critical_section(s)
                    time.sleep(self.k)
        except socket.error as e:
            print(f"Exception ocurred: {e}")
        except Exception as e:
            print(f"Exception ocurred: {e}")

    def send_request(self, s):
        message = f"1|{self.process_id}|{'0'*(self.F-4-len(self.process_id))}"
        s.send(message.encode())

    def wait_for_grant(self, s):
        while True:
            response = s.recv(self.F).decode().strip('|')
            if response.startswith("2"):
                break

    def enter_critical_section(self):
        with open('resultado.txt', 'a') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            f.write(f"{self.process_id}, {timestamp}\n")
