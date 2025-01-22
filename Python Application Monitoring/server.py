import random
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import prometheus_client

app = FastAPI()

# Configuração do middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definição dos contadores do Prometheus
heads_count = prometheus_client.Counter(
    "heads_count",
    "Number of heads",
)

tails_count = prometheus_client.Counter(
    "tails_count",
    "Number of tails",
)

flip_count = prometheus_client.Counter(
    "flip_count",
    "Number of flips",
)

# Rota para realizar os lançamentos de moedas
@app.get("/flip-coins")
async def flip_coins(times: str = Query(..., description="Number of coin flips")):
    # Verifica se 'times' é um número inteiro válido
    if not times.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Parameter 'times' must be an integer"
        )
    
    times_as_int = int(times)
    heads = 0

    # Simula os lançamentos da moeda
    for _ in range(times_as_int):
        if random.randint(0, 1):
            heads += 1
    
    tails = times_as_int - heads

    # Incrementa as métricas do Prometheus
    heads_count.inc(heads)
    tails_count.inc(tails)
    flip_count.inc(times_as_int)

    return {
        "heads": heads,
        "tails": tails,
    }

# Rota para retornar as métricas do Prometheus
@app.get('/metrics')
def get_metrics():
    return Response(
        content=prometheus_client.generate_latest(),
        media_type="text/plain",
    )

# Execução do servidor
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
