#  Rodando em uma rede e porta especifico 


~~~ 
fastapi dev fast_zero/app.py --host 0.0.0.0
~~~ 

ou 

~~~
task run --host 0.0.0.0
~~~


# Httpp  e outros assuntos relacionado

Ele falou mas, não entramos no assunto 


# Mandando o código de status

~~~ python 
@app.get("/", status_code=HTTPStatus.OK)
def read_root():
    return {'message': 'Olá Mundo!'}
~~~

ou podemos 

~~~ python 
@app.get("/", status_code=HTTPStatus.OK)
def read_root():
    return {'message': 'Olá Mundo!'}
~~~


# Documentação automatizada 

Esite dois tipos de documentação 

- Swaggers UX:  que possibilita de interagir diretamente com API atráves da interface, após rodar acesse: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

- Redoc:  ela é mais limpar [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) 



# Pydantic

Ele serve validar os dados danto de entrada e como saída. E serve também como documentação 


## Exemplo Validando o tipo de dados

Criamos `schemas.py` dentro do `fast_zero`


~~~ python 
from pydantic import BaseModel


class Message(BaseModel):
    message: str
~~~~




~~~ python  
from http import HTTPStatus

from fastapi import FastAPI

from fast_zero.schemas import Message

app = FastAPI()


@app.get('/', status_code=HTTPStatus.OK, response_model=Message) #observer
def read_root():
    return {'message': 'Olá Mundo!'}
~~~

Rode ele, modifique `str` para `int` e roder para ver o resultado



**Pydantic** vai ser explorado mais na próxima aula. 