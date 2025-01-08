# Objetivo 

Estamos adquirindo conhecimento atráves da playlist.


## Link 


[https://fastapidozero.dunossauro.com/01/](https://fastapidozero.dunossauro.com/01/)

[https://www.youtube.com/watch?v=WnhDgVLYfx0](https://www.youtube.com/watch?v=WnhDgVLYfx0)



# Minhas notação 

## Configuração 

### Instalação 

Não vou abordar, mas não é um bixo de sete cabeça. 

###  Setando a versão do python

O  `pyenv` serve para nós conseguir escolher a versão do python que queremos trabalhar 


Vamos fazer autualizar e instalar. 
~~~ bash 
pyenv update
pyenv install 3.11:latest
~~~ 

Vamos fazer com utilizer `3.11`, depois vamos verificar se esta correto o carregamento.
~~~ bash 
pyenv local 3.11
python --version
~~~ 

### Poetry

Posso esta falando equivocado, mas é o que vai gerenciar as depêndencia dos pacotes. 

Vamos inicializar o projeto 

~~~ 
poetry new nomeProjeto
~~~

õu 

~~~ 
poetry init 
~~~ 

A diferença que o primeiro já cria o diretorio e nem precisa ficar preenchendo um formulário.

Já o segundo, você já tem o diretório ou projeto, só precisar criar, vai ter uma muitas perguntas a serem respondido

**No caso vamos utilizar `poetry new fast_zero**

Já dentro da pasta, é necessário fazer 

~~~ 
poetry install
~~~ 

#### Adicionando fastapi no poetry

Para que possamos, adicionar  basta fazer

~~~
poetry add fastapi
~~~


### Pequeno teste e um grande passo 

Dentro do diretório `fast_zero\fast_zero`  vamos criar o arquivo `app.py` 
~~~ python
from fastapi import FastAPI 

app = FastAPI()  

@app.get('/')  
def read_root():  
    return {'message': 'Olá Mundo!'}
~~~ 


Antes de nós rodar o programa, precisamos ativar o `env`

#### Ativando o `env`

~~~ bash  
poetry env use python3
source $(poetry env info --path)/bin/activate
~~~

o comando `poetry shell` caiu em **desuso**


#### rodando 

~~~ bash 
fastapi dev fast_zero/app.py
~~~ 

outra forma de conseguimos rodar é utilizar o  `Uvicorn`

~~~ bash 
uvicorn fast_zero.app:app
~~~

### Configuração de desenvolvimento 


Vamos adicionar várias linha no nosso arquivo `pyproject.toml`  e depois rodaremos "tudo junto". Logo, importante seguir até o fim.


#### Ruff

Vai servir para veirifcar o **estilo** do nosso código e verificar a **boas práticas**

~~~
[tool.ruff]
line-length = 79
extend-exclude = ['migrations']

[tool.ruff.lint]
preview = true
select = ['I', 'F', 'E', 'W', 'PL', 'PT']
~~~ 

Leia a documentação!

#### Pytest


Como nome já diz vai servi para nós criamos teste. 

~~~ 
[tool.pytest.ini_options]
pythonpath = "."
addopts = '-p no:warnings'
~~~


#### Taskipy

Vai servir como `tecla de atalho`

~~~ 
[tool.taskipy.tasks]
lint = 'ruff check .; ruff check . --diff'
format = 'ruff check . --fix; ruff format .'
run = 'fastapi dev fast_zero/app.py'
pre_test = 'task lint'
test = 'pytest -s -x --cov=fast_zero -vv'
post_test = 'coverage html'
~~~ 


#### Adicionado tudo isso no poetry


Faça isso com **env desativado**, para isso basta usar o comando `deactivate`
~~~ 
poetry add --group dev pytest pytest-cov taskipy ruff
~~~


**Observação:**

Pode dá erro em relação ao versão do python.

Foi resolvido fazendo:

~~~ 
[tool.poetry.dependencies]
python = "^3.9"
~~~


#### Rodando para ver se deu tudo certo

agora ativa `venv`

~~~
source .venv/bin/activate
~~~

**Rodando simples**

~~~
task run
~~~ 


**Rodando para ver o estilo do código**

~~~
task lint
~~~

**Rodando para formatar o nosso código**

~~~
task format
~~~

Se nós usamos novamente `task lint` vamos verificar que o nosso código vai esta formatado corretamente. 


**Rodando teste**

~~~ 
task test
~~~

~~~
task post_test
~~~ 

O primieo mosta como um resultado simples, já o segundo mostra com mais detalhe, abra ele no navegador.


## Escrevendo um teste para testar 


Vamos criar  `tests/test_app.py`
~~~ 
from http import HTTPStatus

from fastapi.testclient import TestClient

from fast_zero.app import app


def test_root_deve_retornar_ok_e_ola_mundo():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Olá Mundo!"}

~~~
