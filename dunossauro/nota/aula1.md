# Configuração

### Instalação

Não vou abordar aqui, mas não é um bicho de sete cabeças.

### Definindo a versão do Python

O `pyenv` serve para escolhermos a versão do Python que queremos trabalhar.

Vamos atualizar e instalar:  
~~~bash
pyenv update
pyenv install 3.11:latest
~~~

Depois de instalar, configuramos para usar a versão `3.11` e verificamos se foi carregada corretamente:
~~~bash
pyenv local 3.11
python --version
~~~

### Poetry

Posso estar equivocado, mas o Poetry gerencia as dependências dos pacotes.

Para inicializar o projeto, temos duas opções:  
~~~bash
poetry new nomeProjeto
~~~  
ou  
~~~bash
poetry init
~~~

A diferença é que o primeiro já cria o diretório do projeto e não precisa preencher formulário.  
Já o segundo serve para um projeto já existente; você preenche várias perguntas para configurar.

**No nosso caso, usaremos `poetry new fast_zero`.**

Dentro da pasta, é necessário instalar as dependências:
~~~bash
poetry install
~~~

#### Adicionando o FastAPI ao Poetry

Para adicionar, basta rodar:
~~~bash
poetry add fastapi
~~~

### Pequeno teste e um grande passo

Dentro do diretório `fast_zero/fast_zero`, vamos criar o arquivo `app.py` com o seguinte código:
~~~python
from fastapi import FastAPI 

app = FastAPI()  

@app.get("/")  
def read_root():  
    return {"message": "Olá Mundo!"}
~~~

Antes de rodar o programa, precisamos ativar o ambiente virtual (`env`).

#### Ativando o `env`

~~~bash
poetry env use python3
source $(poetry env info --path)/bin/activate
~~~

O comando `poetry shell` caiu em **desuso**.

#### Executando o código

~~~bash
fastapi dev fast_zero/app.py
~~~

Outra forma é utilizando o `Uvicorn`:
~~~bash
uvicorn fast_zero.app:app
~~~

### Configuração de desenvolvimento

Vamos adicionar várias linhas no arquivo `pyproject.toml` e executar tudo junto no final. Siga as etapas até o fim.

#### Ruff

O Ruff será usado para verificar o **estilo** do código e as **boas práticas**:
~~~toml
[tool.ruff]
line-length = 79
extend-exclude = ["migrations"]

[tool.ruff.lint]
preview = true
select = ["I", "F", "E", "W", "PL", "PT"]
~~~

Consulte a documentação para mais detalhes!

#### Pytest

O Pytest será utilizado para criar testes:
~~~toml
[tool.pytest.ini_options]
pythonpath = "."
addopts = "-p no:warnings"
~~~

#### Taskipy

O Taskipy servirá como um **atalho** para comandos:
~~~toml
[tool.taskipy.tasks]
lint = "ruff check .; ruff check . --diff"
format = "ruff check . --fix; ruff format ."
run = "fastapi dev fast_zero/app.py"
pre_test = "task lint"
test = "pytest -s -x --cov=fast_zero -vv"
post_test = "coverage html"
~~~

#### Adicionando as dependências no Poetry

Certifique-se de estar com o ambiente virtual desativado (`deactivate`) antes de rodar:
~~~bash
poetry add --group dev pytest pytest-cov taskipy ruff
~~~

**Observação:**  
Pode ocorrer um erro relacionado à versão do Python. Caso aconteça, resolva alterando no `pyproject.toml`:
~~~toml
[tool.poetry.dependencies]
python = "^3.9"
~~~

#### Testando a configuração

Ative o ambiente virtual novamente:
~~~bash
source .venv/bin/activate
~~~

**Rodando a aplicação:**
~~~bash
task run
~~~

**Verificando o estilo do código:**
~~~bash
task lint
~~~

**Formatando o código automaticamente:**
~~~bash
task format
~~~

Após formatar, se rodarmos novamente `task lint`, veremos que o código estará corrigido.

**Rodando os testes:**
~~~bash
task test
~~~
~~~bash
task post_test
~~~

O primeiro comando mostra um resultado simples, enquanto o segundo gera um relatório mais detalhado em HTML, que pode ser aberto no navegador.

## Escrevendo um teste

Vamos criar o arquivo `tests/test_app.py` com o seguinte código:
~~~python
from http import HTTPStatus
from fastapi.testclient import TestClient
from fast_zero.app import app


def test_root_deve_retornar_ok_e_ola_mundo():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Olá Mundo!"}
~~~