from coordinator import Coordinator
from process import Process
import threading

def start_process(process_id, r, k):
    p = Process(process_id, r=r, k=k)
    p.start()

if __name__ == "__main__":
    coordinator = Coordinator()
    threading.Thread(target=coordinator.start).start()

    # Iniciar processos
    process_count = 3
    r = 5
    k = 2
    for i in range(1, process_count + 1):
        threading.Thread(target=start_process, args=(str(i), r, k)).start()