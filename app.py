
from fastapi import FastAPI, HTTPException
from fastapi import Path as ApiPath
from prometheus_client import Counter, generate_latest, Gauge
from prometheus_client import CONTENT_TYPE_LATEST
import hashlib, os, time, threading, random
from fastapi.responses import PlainTextResponse
from pathlib import Path
import psutil
import shutil

# Inicialização da app
app = FastAPI(
    title="Trouble Box",
    description="Simulador de carga para testes com Kubernetes e Observabilidade",
    version="1.0.0",
    contact={
        "name": "Troublebox aPP",
        "url": "https://rmnobarra.github.io",
        "email": "rmnobarra@gmail.com"
    },
)

# Métricas Prometheus
REQUEST_COUNTER = Counter("troublebox_orders_total", "Total de pedidos processados")
CPU_LOAD = Gauge("troublebox_cpu_load", "Carga de CPU simulada")
MEMORY_LOAD = Gauge("troublebox_memory_load", "Uso de memória simulado")
DISK_USAGE = Gauge("troublebox_disk_usage", "Uso de disco simulado (arquivos criados)")
DISK_USAGE_PERCENT = Gauge("troublebox_disk_usage_percent", "Uso percentual real do volume /orders")
RPS = Gauge("troublebox_rps", "Pedidos simulados por segundo (todos)")


# Controle interno de RPS
_request_count_last_second = 0
_request_count_lock = threading.Lock()

# Variáveis para controlar o load atual
current_cpu_load = 0.0005
current_memory_load = 0.0005
load_lock = threading.Lock()

# Modos de carga
MODES = {
    "normal": 1,
    "hardcore": 5,
    "nightmare": 10
}

# Diretório para arquivos
ORDERS_DIR = Path("orders")
ORDERS_DIR.mkdir(exist_ok=True)

def register_request():
    global _request_count_last_second
    with _request_count_lock:
        _request_count_last_second += 1
    REQUEST_COUNTER.inc()

@app.get("/healthz", summary="Healthcheck", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/metrics", response_class=PlainTextResponse, summary="Métricas Prometheus", tags=["Observabilidade"])
def metrics():
    return generate_latest()

@app.post("/order/{mode}", summary="Simula pedido", tags=["Pedidos"])
def order(
    mode: str = ApiPath(..., description="Modo de carga: normal, hardcore, nightmare")
):
    if mode not in MODES:
        raise HTTPException(status_code=400, detail="Modo inválido")

    count_map = {
        "normal": 100,
        "hardcore": 10_000,
        "nightmare": 1_000_000
    }

    num_pedidos = count_map[mode]
    CPU_LOAD.set(MODES[mode])
    MEMORY_LOAD.set(MODES[mode])

    def process_orders_parallel(num_pedidos, modo, workers=10):
        def worker(start, end):
            for i in range(start, end):
                if i % 1000 == 0:
                    print(f"[manual:{modo}] Pedido {i}/{num_pedidos}")
                simulate_cpu(0.0005)
                simulate_memory(0.0005)
                simulate_disk(modo)
                register_request()

        batch = num_pedidos // workers
        threads = []
        for w in range(workers):
            start = w * batch
            end = (w + 1) * batch if w < workers - 1 else num_pedidos
            t = threading.Thread(target=worker, args=(start, end))
            threads.append(t)
            t.start()

    threading.Thread(target=process_orders_parallel, args=(num_pedidos, mode)).start()

    return {
        "status": "simulando pedidos em segundo plano",
        "mode": mode,
        "quantidade": num_pedidos
    }

@app.post("/load/cpu/{mode}", summary="Carga de CPU", tags=["Carga"])
def cpu_load(
    mode: str = ApiPath(..., description="Modo de carga de CPU: normal, hardcore, nightmare")
):
    global current_cpu_load
    if mode not in MODES:
        raise HTTPException(status_code=400, detail="Modo inválido")
    
    intensity = MODES[mode]
    with load_lock:
        current_cpu_load = intensity
    
    # Define o valor da métrica imediatamente aqui também para garantir
    CPU_LOAD.set(intensity * 10)
    
    threading.Thread(target=simulate_cpu_sustained, args=(intensity,)).start()
    return {"status": "simulando carga de CPU", "mode": mode, "intensity": intensity}

@app.post("/load/memory/{mode}", summary="Carga de Memória", tags=["Carga"])
def memory_load(
    mode: str = ApiPath(..., description="Modo de carga de memória: normal, hardcore, nightmare")
):
    global current_memory_load
    if mode not in MODES:
        raise HTTPException(status_code=400, detail="Modo inválido")
    
    intensity = MODES[mode]
    with load_lock:
        current_memory_load = intensity
    
    # Define o valor da métrica imediatamente aqui também para garantir
    MEMORY_LOAD.set(intensity * 10)
    
    threading.Thread(target=simulate_memory_sustained, args=(intensity,)).start()
    return {"status": "simulando carga de memória", "mode": mode, "intensity": intensity}

@app.post("/load/disk/{mode}", summary="Carga de Disco", tags=["Carga"])
def disk_load(
    mode: str = ApiPath(..., description="Modo de carga de disco: normal, hardcore, nightmare")
):
    if mode not in MODES:
        raise HTTPException(status_code=400, detail="Modo inválido")
    threading.Thread(target=simulate_disk, args=(mode,)).start()
    return {"status": "simulando carga de disco", "mode": mode}

@app.post("/killswitch", summary="Killswitch", tags=["Controle"])
def killswitch():
    os._exit(1)

def simulate_cpu_sustained(intensity, duration=60):
    """Simulate CPU load that sustains for a longer period"""
    # Não precisamos definir a métrica manualmente aqui, pois vamos usar o valor real
    # do uso de CPU detectado pelo psutil
    end_time = time.time() + duration
    
    # Maior intensidade gera mais carga em paralelo
    threads = []
    num_threads = int(intensity * 2)  # Ajuste conforme necessário
    
    # Criar threads para gerar carga de CPU baseada na intensidade
    for _ in range(num_threads):
        t = threading.Thread(target=lambda: cpu_work_loop(end_time))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Aguardar a conclusão de todas as threads
    for t in threads:
        t.join(timeout=duration + 1)  # timeout para evitar bloqueio infinito

# Função para gerar carga de CPU real
def cpu_work_loop(end_time):
    while time.time() < end_time:
        # Trabalho intensivo de CPU
        _ = [i**2 for i in range(10000)]
        # Pequena pausa para evitar travamento completo do sistema
        time.sleep(0.001)

def simulate_memory_sustained(intensity, duration=60):
    """Simulate memory load that sustains for a longer period"""
    # Set the load metric immediately - use higher intensity value to make the effect visible
    real_intensity = intensity * 10
    MEMORY_LOAD.set(real_intensity)
    end_time = time.time() + duration
    
    # Create a memory chunk that will stay for the duration
    main_memory_block = bytearray(int(real_intensity * 500_000))
    
    while time.time() < end_time:
        # Refresh metric periodically to ensure it stays high
        MEMORY_LOAD.set(real_intensity)
        simulate_memory(intensity, update_metric=False)
        # Small sleep
        time.sleep(0.5)
    
    # Clean up the main memory block at the end
    del main_memory_block

def simulate_cpu(intensity, update_metric=True):
    """
    Simulate CPU load. If update_metric is True (default), 
    also update the CPU_LOAD metric.
    """
    # Only update the metric if requested
    if update_metric:
        # Use the global lock to safely update current_cpu_load
        with load_lock:
            CPU_LOAD.set(intensity)
    
    end = time.time() + intensity
    while time.time() < end:
        _ = sum(i * i for i in range(10000))

def simulate_memory(intensity, update_metric=True):
    """
    Simulate memory load. If update_metric is True (default), 
    also update the MEMORY_LOAD metric.
    """
    # Only update the metric if requested
    if update_metric:
        # Use the global lock to safely update current_memory_load
        with load_lock:
            MEMORY_LOAD.set(intensity)
    
    dummy = bytearray(int(intensity * 100_000))
    time.sleep(0.01)
    del dummy

def simulate_disk(mode):
    timestamp = int(time.time() * 1000)
    filename = ORDERS_DIR / f"order_{mode}_{timestamp}.txt"
    content = hashlib.sha256(os.urandom(1024)).hexdigest()
    with open(filename, "w") as f:
        f.write(content)
    DISK_USAGE.inc()

# Função para obter o uso real de CPU
def get_cpu_usage():
    return psutil.cpu_percent(interval=0.1)

# Função para obter o uso real de memória
def get_memory_usage():
    return psutil.virtual_memory().percent

# Loop para atualizar métricas reais de recurso e RPS
def update_metrics_loop():
    global _request_count_last_second
    while True:
        # Atualiza RPS
        with _request_count_lock:
            RPS.set(_request_count_last_second)
            _request_count_last_second = 0
        
        # Atualiza métricas de CPU e memória com valores reais
        cpu_usage = get_cpu_usage()
        mem_usage = get_memory_usage()
        
        # Só atualiza se os testes de carga não estiverem ativos
        with load_lock:
            if CPU_LOAD._value.get() < 10.0:  # Se não estiver em teste de carga
                CPU_LOAD.set(cpu_usage)
            if MEMORY_LOAD._value.get() < 10.0:  # Se não estiver em teste de carga
                MEMORY_LOAD.set(mem_usage)
        
        time.sleep(1)

# Geração contínua de tráfego leve
def generate_traffic():
    modos = list(MODES.keys())
    while True:
        quantidade = random.randint(1, 10)
        for _ in range(quantidade):
            modo = random.choice(modos)
            # Não redefinir métricas no tráfego automático se estiverem com valores altos
            # Apenas ajuste as métricas se seus valores atuais forem baixos
            if CPU_LOAD._value.get() < 1.0:  # Valor baixo
                simulate_cpu(0.0005)
            if MEMORY_LOAD._value.get() < 1.0:  # Valor baixo
                simulate_memory(0.0005)
            simulate_disk(modo)
            register_request()
        print(f"[auto] Gerou {quantidade} requisições simuladas")
        time.sleep(1)


import shutil

def update_disk_usage_loop():
    while True:
        try:
            total, used, free = shutil.disk_usage("./orders")
            usage_percent = (used / total) * 100
            DISK_USAGE_PERCENT.set(usage_percent)
        except Exception as e:
            print(f"Erro ao calcular uso de disco: {e}")
        time.sleep(5)


# Início das threads de fundo
threading.Thread(target=generate_traffic, daemon=True).start()
threading.Thread(target=update_metrics_loop, daemon=True).start()
threading.Thread(target=update_disk_usage_loop, daemon=True).start()

