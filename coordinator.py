import socket
import threading
import time
import queue

class Coordinator:
    def __init__(self, host='127.0.0.1', port=5000, F=10):
        self.host = host
        self.port = port
        self.F = F
        self.queue = queue.Queue()
        self.sockets = {}
        self.lock = threading.Lock()
        self.logs = []
        self.process_count = {}

    def start(self):
        threading.Thread(target=self.handle_connections).start()
        threading.Thread(target=self.handle_requests).start()
        threading.Thread(target=self.terminal_interface).start()

    def handle_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Coordinator is listening on {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                process_id = conn.recv(self.F).decode().strip('|')
                self.sockets[process_id] = conn
                self.process_count[process_id] = 0
                print(f"Process {process_id} connected.")

    def handle_requests(self):
        while True:
            if not self.queue.empty():
                process_id = self.queue.get()
                self.lock.acquire()
                self.send_grant(process_id)
                time.sleep(1)  # Simulate critical section duration
                self.send_release(process_id)
                self.lock.release()

    def send_grant(self, process_id):
        message = f"2|{process_id}|{'0'*(self.F-4-len(process_id))}"
        self.sockets[process_id].send(message.encode())
        self.log_message('GRANT', process_id)

    def send_release(self, process_id):
        message = f"3|{process_id}|{'0'*(self.F-4-len(process_id))}"
        self.sockets[process_id].send(message.encode())
        self.log_message('RELEASE', process_id)

    def log_message(self, message_type, process_id):
        timestamp = time.time()
        self.logs.append((timestamp, message_type, process_id))
        if message_type == 'GRANT':
            self.process_count[process_id] += 1
        print(f"{timestamp}: {message_type} sent to Process {process_id}")

    def terminal_interface(self):
        while True:
            command = input("Enter command: ")
            if command == "1":
                self.print_queue()
            elif command == "2":
                self.print_process_count()
            elif command == "3":
                self.shutdown()
                break

    def print_queue(self):
        print("Current Queue: ", list(self.queue.queue))

    def print_process_count(self):
        print("Process Count: ", self.process_count)

    def shutdown(self):
        print("Shutting down coordinator.")
        for conn in self.sockets.values():
            conn.close()
        exit(0)
