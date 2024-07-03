"""
States disponíveis:
RELEASED - Aguardando requisições
WANTED - Pretende entrar na área crítica
HELD - Pode entrar na seção crítica
REQUEST - Envia mensagem pedindo acesso ao recurso na area crítica
REPLY - Envia resposta ao processo que solicitou acesso
ELECTION - Envia mensagem para realizar eleição
COORDINATOR - Novo líder envia mensagem para ajustar líder dos processos
CHECK_LEADER - Envia mensagem para verificar se líder está vivo
LEADER_ALIVE - Líder retorna mensagem se estiver vivo
"""

# Os valores abaixo garantem a aleatoriedade enquanto os processos rodam
MIN_RUNNING_TIME = 0.2
MAX_RUNNING_TIME = 0.6
MIN_CRITICAL_TIME = 0.2
MAX_CRITICAL_TIME = 0.6

import threading
import time
import random

from distributed_algorithms.lamport_clock import LamportClock

class Process(threading.Thread):
    def __init__(self, pid, n_processes, processes):
        super().__init__()
        self.pid = pid
        self.n_processes = n_processes
        self.processes = processes
        self.clock = LamportClock()
        self.request_queue = []
        self.reply_count = 0
        self.replies = []
        self.state = 'RELEASED'
        self.timestamp = 0
        self.leader = None
        self.running = True
        self.leader_alive = True

    def run(self):
        if self.leader is None:
            self.start_election()

        while self.running:
            time.sleep(random.uniform(MIN_RUNNING_TIME, MAX_RUNNING_TIME))
            if self.state == 'RELEASED':
                self.request_critical_section()
            elif self.state == 'HELD':
                self.use_critical_section()

            self.check_leader()

            while self.request_queue:
                sender, timestamp, message_type = self.request_queue.pop(0)
                self.handle_message(sender, timestamp, message_type)

        print(f"Process {self.pid} has stopped running")

    def request_critical_section(self):
        if not self.running:
            return
        self.state = 'WANTED'
        self.reply_count = 0
        self.replies = []
        self.timestamp = self.clock.tick()
        print(f"Process {self.pid} requests critical section at time {self.timestamp}")
        for i in range(self.n_processes):
            if i != self.pid:
                self.send_message(i, 'REQUEST', self.timestamp)

    def handle_message(self, sender, timestamp, message_type):
        self.clock.update(timestamp)
        print(f"Process {self.pid} received {message_type} from Process {sender} at time {self.clock.get_time()}")

        # Solicita acesso ao recurso
        if message_type == 'REQUEST':
            self.clock.tick()
            if self.state == 'HELD' or (self.state == 'WANTED' and (self.timestamp < timestamp or (self.timestamp == timestamp and self.pid < sender))):
                self.replies.append((sender, timestamp))
            else:
                self.send_message(sender, 'REPLY', self.clock.get_time())

        # Resposta demais processos de acesso ao recurso
        elif message_type == 'REPLY':
            self.clock.tick()
            self.reply_count += 1
            if self.reply_count == self.n_processes - 1:
                self.state = 'HELD'

        # Realizar eleicao
        elif message_type == 'ELECTION':
            self.clock.tick()
            if sender > self.pid:
                self.start_election()

        # Mensagem do coordenador
        elif message_type == 'COORDINATOR':
            self.clock.tick()
            self.leader = sender
            print(f"Process {self.pid} recognizes Process {self.leader}")

        # Envia mensagem para verificar se o líder está vivo
        elif message_type == 'CHECK_LEADER':
            self.clock.tick()
            self.send_message(sender, 'LEADER_ALIVE', self.clock.get_time())

        # Recebe confirmacao do líder vivo e seta leader_alive como true
        elif message_type == 'LEADER_ALIVE':
            self.clock.tick()
            self.leader_alive = True

    def use_critical_section(self):
        if not self.running:
            return
        print(f"Process {self.pid} is in critical section at time {self.clock.get_time()}")
        time.sleep(random.uniform(MIN_CRITICAL_TIME, MAX_CRITICAL_TIME))
        self.state = 'RELEASED'
        self.clock.tick()
        print(f"Process {self.pid} exits critical section at time {self.clock.get_time()}")
        for reply in self.replies:
            self.send_message(reply[0], 'REPLY', self.clock.get_time())
        self.replies = []

    def send_message(self, recipient, message_type, timestamp):
        if self.running and recipient < len(self.processes):
            self.processes[recipient].receive_message(self.pid, timestamp, message_type)

    def receive_message(self, sender, timestamp, message_type):
        self.request_queue.append((sender, timestamp, message_type))
        self.clock.update(timestamp)
        return True

    def start_election(self):
        print(f"Process {self.pid} is starting an election")
        higher_processes = [p for p in range(self.pid + 1, self.n_processes) if self.processes[p].running]
        if not higher_processes:
            self.leader = self.pid
            self.announce_leader()
        else:
            for p in higher_processes:
                self.send_message(p, 'ELECTION', self.clock.get_time())
        self.state = "RELEASED"

    def announce_leader(self):
        for p in range(self.n_processes):
            if p != self.pid:
                self.send_message(p, 'COORDINATOR', self.clock.get_time())
        print(f"Process {self.pid} announces itself as leader at time")
        self.state = "RELEASED"

    def check_leader(self):
        if self.leader == self.pid:
            self.state = "RELEASED"
            return

        elif self.leader is None:
            print(f"No leader is currently elected. Process {self.pid} is starting a new election")
            self.start_election()
            return
        
        else:
            if not self.processes[self.leader].running:
                self.leader_alive = False
            else:
                self.leader_alive = True

            self.send_message(self.leader, 'CHECK_LEADER', self.clock.get_time())
            
            if not self.leader_alive:
                print(f"Leader {self.leader} is not responding. Process {self.pid} is starting a new election")
                self.n_processes = self.n_processes-1
                self.start_election()
                