import socket
import threading
import time
import queue
import logging
import os

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
                    if not process_id:
                        logging.warning("Received empty process ID.")
                        conn.close()
                        continue
                    with self.lock:
                        if process_id not in self.sockets:
                            self.sockets[process_id] = conn
                            self.process_count[process_id] = 0
                            logging.info(f"Process {process_id} connected from {addr}.")
                            self.queue.put(process_id)
                            logging.info(f"Added Process {process_id} to the queue. Queue length: {self.queue.qsize()}.")
                        else:
                            logging.info(f"Process {process_id} is already connected. Ignoring connection.")
                except Exception as e:
                    logging.error(f"Error accepting connection: {e}")

    def handle_requests(self):
        while not self.shutdown_event.is_set():
            if not self.queue.empty():
                process_id = self.queue.get()
                with self.lock:
                    if process_id in self.sockets:
                        logging.info(f"Processing request from Process {process_id}.")
                        self.send_grant(process_id)
                        time.sleep(1)  # Simulate critical section duration
                        self.send_release(process_id)
                    else:
                        logging.warning(f"Process {process_id} not found in sockets. Skipping.")
            else:
                time.sleep(0.1)  # Sleep briefly to prevent busy waiting

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
            # Re-queue the process for the next REQUEST
            self.queue.put(process_id)
            logging.info(f"Re-queued process {process_id}. Queue length: {self.queue.qsize()}.")
        except Exception as e:
            logging.error(f"Error sending RELEASE to Process {process_id}: {e}")

    def log_message(self, message_type, process_id):
        timestamp = time.time()
        self.logs.append((timestamp, message_type, process_id))
        logging.info(f"{message_type} sent to Process {process_id}. Queue length: {self.queue.qsize()}. Process Count: {self.process_count.get(process_id, 0)}")

    def terminal_interface(self):
        print("Welcome. Please select an action:\n1 - Print Queue\n2 - Print Process Count\n3 - Shutdown Process")
        command = input("Enter command: ")
        match command:    
            case "1":
                self.print_queue()
            case "2":
                self.print_process_count()
            case "3":
                self.shutdown()
            case _:
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
            try:
                conn.close()
            except Exception as e:
                logging.error(f"Error closing connection: {e}")

        for handler in logging.getLogger().handlers:
            handler.flush()
            handler.close()

        log_file = 'coordinator.log'
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logging.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logging.error(f"Error deleting log file: {e}")        
        exit(0)