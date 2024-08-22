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
                # Enviar o ID do processo, preenchendo com zeros à esquerda
                s.send(f"{self.process_id}|{'0'*(self.F-len(self.process_id)-1)}".encode())

                for _ in range(self.r):
                    self.send_request(s)
                    self.wait_for_grant(s)
                    self.enter_critical_section()
                    time.sleep(self.k)
        except ConnectionResetError:
            print("Erro: A conexão com o coordenador foi resetada.")
        except Exception as e:
            print(f"Erro inesperado: {e}")

    def send_request(self, s):
        # Enviar a solicitação de acesso à região crítica
        message = f"1|{self.process_id}|{'0'*(self.F-4-len(self.process_id))}"
        s.send(message.encode())

    def wait_for_grant(self, s):
        while True:
            try:
                response = s.recv(self.F).decode().strip('|')
                # Verificar se a resposta é uma concessão (tipo 2)
                if response.startswith("2|"):
                    break
            except ConnectionResetError:
                print("Erro: A conexão foi resetada pelo coordenador.")
                break
            except Exception as e:
                print(f"Erro ao esperar pela permissão: {e}")
                break

    def enter_critical_section(self):
        # Escrever no arquivo resultado.txt com hora atual incluindo milissegundos
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + f".{int(time.time() * 1000) % 1000:03d}"
        with open('resultado.txt', 'a') as f:
            f.write(f"{self.process_id}, {timestamp}\n")

