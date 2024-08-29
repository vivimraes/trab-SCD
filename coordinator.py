import socket
import threading
import time
import queue
import logging

# Configure logging
logging.basicConfig(
    filename='coordinator.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
        self.shutdown_event = threading.Event()

    def start(self):
        threading.Thread(target=self.handle_connections, daemon=True).start()
        threading.Thread(target=self.handle_requests, daemon=True).start()
        self.terminal_interface()

    def handle_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            logging.info(f"Coordinator is listening on {self.host}:{self.port}")
            while not self.shutdown_event.is_set():
                try:
                    conn, addr = s.accept()
                    process_id = conn.recv(self.F).decode().strip('|')
                    with self.lock:
                        self.sockets[process_id] = conn
                        self.process_count[process_id] = 0
                    logging.info(f"Process {process_id} connected from {addr}.")
                    self.queue.put(process_id)
                    logging.info(f"Added Process {process_id} to the queue.")
                except Exception as e:
                    logging.error(f"Error accepting connection: {e}")

    def handle_requests(self):
        while not self.shutdown_event.is_set():
            if not self.queue.empty():
                process_id = self.queue.get()
                with self.lock:
                    logging.info(f"Processing request from Process {process_id}.")
                    self.send_grant(process_id)
                    time.sleep(1)  # Simulate critical section duration
                    self.send_release(process_id)

    def send_grant(self, process_id):
        message = f"2|{process_id}|{'0'*(self.F-4-len(process_id))}"
        try:
            self.sockets[process_id].send(message.encode())
            self.log_message('GRANT', process_id)
        except Exception as e:
            logging.error(f"Error sending GRANT to Process {process_id}: {e}")

    def send_release(self, process_id):
        message = f"3|{process_id}|{'0'*(self.F-4-len(process_id))}"
        try:
            self.sockets[process_id].send(message.encode())
            self.log_message('RELEASE', process_id)
        except Exception as e:
            logging.error(f"Error sending RELEASE to Process {process_id}: {e}")

    def log_message(self, message_type, process_id):
        timestamp = time.time()
        self.logs.append((timestamp, message_type, process_id))
        logging.info(f"{message_type} sent to Process {process_id}. Queue length: {self.queue.qsize()}. Process Count: {self.process_count.get(process_id, 0)}")

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
            else:
                print("Unknown command. Please enter '1', '2', or '3'.")

    def print_queue(self):
        with self.lock:
            print("Current Queue: ", list(self.queue.queue))

    def print_process_count(self):
        with self.lock:
            print("Process Count: ", self.process_count)

    def shutdown(self):
        print("Shutting down coordinator.")
        logging.info("Shutting down coordinator.")
        self.shutdown_event.set()
        for conn in self.sockets.values():
            conn.close()
        exit(0)
