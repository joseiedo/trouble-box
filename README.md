# Trouble Box 🧰

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)

**Trouble Box** é um simulador de carga projetado para testes com Kubernetes e ferramentas de observabilidade. Gera carga controlada de CPU, memória e disco, ideal para testar escalabilidade, monitoramento e resiliência de sistemas.

## 📋 Funcionalidades

- **Simulação de Carga de CPU**: Gera diferentes níveis de uso de CPU
- **Simulação de Carga de Memória**: Aloca memória em diferentes quantidades
- **Simulação de Carga de Disco**: Cria arquivos para simular uso de disco
- **Simulação de Pedidos**: Processa pedidos em massa com carga controlada
- **Métricas Prometheus**: Expõe métricas para monitoramento
- **Monitor de Recursos Reais**: Monitora o uso real de CPU e memória

## 🚀 Modos de Carga

O simulador oferece três níveis de intensidade:

- **Normal**: Carga leve (intensidade 1)
- **Hardcore**: Carga média (intensidade 5)
- **Nightmare**: Carga pesada (intensidade 10)

## 📊 Métricas Disponíveis

- `troublebox_orders_total`: Total de pedidos processados
- `troublebox_cpu_load`: Carga de CPU simulada
- `troublebox_memory_load`: Uso de memória simulado
- `troublebox_disk_usage`: Uso de disco simulado (arquivos criados)
- `troublebox_rps`: Pedidos simulados por segundo

## 🛠️ Requisitos

- Python 3.7+
- FastAPI
- Uvicorn
- Prometheus Client
- psutil

## 🔧 Instalação

Clone o repositório e instale as dependências:

```bash
git clone <repositório>
cd trouble-box
pip install -r requirements.txt
```

## ▶️ Executando a Aplicação

Para iniciar a aplicação localmente:

```bash
uvicorn app:app --reload
```

Para iniciar em containers:

```bash
docker build -t trouble-box:latest .
docker run -p 8000:8000 trouble-box:latest
```

Para deploy no Kubernetes:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 🧪 Utilizando a API

### Healthcheck

```
GET /healthz
```

Exemplo:
```bash
curl http://localhost:8000/healthz
```

### Métricas Prometheus

```
GET /metrics
```

Exemplo:
```bash
curl http://localhost:8000/metrics
```

### Simular Pedidos

```
POST /order/{mode}
```

Onde `mode` pode ser: `normal`, `hardcore` ou `nightmare`.

Exemplo:
```bash
curl -X POST http://localhost:8000/order/normal
```

### Simular Carga de CPU

```
POST /load/cpu/{mode}
```

Exemplo:
```bash
curl -X POST http://localhost:8000/load/cpu/hardcore
```

### Simular Carga de Memória

```
POST /load/memory/{mode}
```

Exemplo:
```bash
curl -X POST http://localhost:8000/load/memory/hardcore
```

### Simular Carga de Disco

```
POST /load/disk/{mode}
```

Exemplo:
```bash
curl -X POST http://localhost:8000/load/disk/hardcore
```

### Killswitch (Encerrar a aplicação)

```
POST /killswitch
```

Exemplo:
```bash
curl -X POST http://localhost:8000/killswitch
```

## 📈 Monitoramento

Para monitorar a aplicação, configure o Prometheus para raspar as métricas expostas em `/metrics`.

Exemplo de configuração no `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'trouble-box'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:8000']
```

## 🔍 Dicas para testes

1. **Teste de Escalabilidade**: Execute uma carga `nightmare` e observe como o Kubernetes lida com a escala automática (se configurado)
2. **Teste de Alertas**: Configure alertas no Prometheus para disparar quando o uso de CPU ou memória exceder determinados limites
3. **Teste de Resiliência**: Use o endpoint `/killswitch` para simular falhas e testar recuperação automática

## 🧩 Estrutura do Projeto

- `app.py`: Aplicação principal FastAPI
- `requirements.txt`: Dependências do projeto
- `Dockerfile`: Configuração para containerização
- `k8s/`: Manifests para deploy no Kubernetes
- `orders/`: Diretório onde são armazenados os arquivos gerados pelo teste de disco

## 🔄 CI/CD com GitHub Actions

Este projeto inclui configuração para CI/CD com GitHub Actions que automatiza o build e push da imagem Docker para o DockerHub.

### Configuração dos Segredos

Para que o workflow funcione, você precisa adicionar os seguintes segredos nas configurações do GitHub:

1. Vá para seu repositório no GitHub
2. Navegue até "Settings" > "Secrets and variables" > "Actions"
3. Adicione os seguintes segredos:
   - `DOCKERHUB_USERNAME`: Seu nome de usuário do DockerHub
   - `DOCKERHUB_TOKEN`: Seu token de acesso do DockerHub (não use sua senha, crie um token de acesso)

### Processo de CI/CD

- Cada push para a branch `main` gera uma nova imagem com a tag `latest`
- Criar uma tag com formato `v*` (ex: v1.0.0) gerará uma imagem com essa tag específica
- Pull requests são verificadas com build de teste, mas sem push para o DockerHub

## 📄 Licença

Este projeto está licenciado sob a licença MIT.

---

Desenvolvido para testes de observabilidade e monitoramento em ambientes Kubernetes.
