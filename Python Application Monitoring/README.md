

# Vídeo

Estamos estudando através desse vídeo: [https://www.youtube.com/watch?v=x3bSuGH8R28](https://www.youtube.com/watch?v=x3bSuGH8R28)

## O que ele faz?

Ele simula uma moeda (cara ou coroa) e, com o Prometheus, realiza o monitoramento.

## Como Rodar?

Após fazer o Git Clone, dentro do diretório, execute o comando:
~~~ bash 
docker-compose up --build 
~~~

### Simulação de moeda

Acesse:
~~~ 
http://0.0.0.0:5000/flip-coins?times=100
~~~ 
Onde `times=100` representa a quantidade de lançamentos.

### Relatório

Acesse:
~~~ 
http://0.0.0.0:5000/metrics
~~~ 

Ou acesse o Prometheus diretamente em:
~~~
http://0.0.0.0:9090
~~~

Exemplo de entrada:
- `flip_count_created`
- Ele autocompleta, então é possível visualizar as opções.

---

# Completo: OK