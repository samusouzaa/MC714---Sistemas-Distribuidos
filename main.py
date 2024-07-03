NUMERO_PROCESSOS = 3

from distributed_algorithms.process import Process
import time

def main():

    processes = [Process(i, NUMERO_PROCESSOS, []) for i in range(NUMERO_PROCESSOS)]
    
    for process in processes:
        process.processes = processes
    
    # Inicia os processos juntos
    for process in processes:
        process.start()

    # Deixa os processos gerarem logs de acesso
    time.sleep(20)

    # Simula parada do Líder
    for process in processes:
        if process.leader != None:
            leader = process.leader
            break
        
    print(f"Stopping the leader Process:{leader}")
    processes[int(leader)].running = False
    processes[int(leader)].join()
    # Decta a falha e elege novo líder
    time.sleep(20)

    # Volta a rodar o processo
    print(f"Return the leader Process:{leader}")
    processes[int(leader)] = Process(leader, NUMERO_PROCESSOS, processes)
    processes[int(leader)].start()

    # Deixa estabilizar
    time.sleep(10)

    for process in processes:
        process.running = False
        process.join()

if __name__ == "__main__":
    main()
