

# Integrando com Banco de Dados

## Instalação

~~~bash
poetry add sqlalchemy
~~~

## ORM

Em resumo, **ORM** serve para que você não precise trabalhar diretamente com o banco de dados. Em vez disso, você trabalha com Orientação a Objetos.

Crie o arquivo `model.py` dentro do diretório `fast_zero`:
~~~python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()

@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
~~~

Essas duas linhas:
~~~python
table_registry = registry()

@table_registry.mapped_as_dataclass
~~~ 

Servem para criar nosso banco de dados e também para facilitar os testes. Estude um pouco mais sobre elas, pois serão úteis.

---

### `Mapped`

O **`Mapped`** serve para mapear os atributos da classe Python para as colunas do banco de dados. Ele indica o tipo de dado com o qual o banco está lidando. Em bancos de dados, existem tipos específicos (como `INTEGER`, `VARCHAR` etc.), enquanto no Python usamos tipos mais gerais como `int` ou `str`.

Exemplo: No Python, lidamos com o atributo **`id`** como um inteiro (`int`), mas no banco de dados, ele será interpretado como uma **chave primária** (`PRIMARY KEY`).

- **`init=False`**: Indica que o valor desse atributo será preenchido automaticamente pelo banco de dados.
- **`unique=True`**: Garante que os valores dessa coluna sejam únicos (não podem se repetir).
- **`server_default=func.now()`**: Configura o valor padrão como a data e hora atual do servidor.

---

### Testando até o momento

No terminal:
~~~bash
python -i fast_zero/model.py
~~~

Teste a criação de um objeto:
~~~python
User("Ricardo", "senha", "email@gmail.com")
~~~

---

## Testando a Criação da Tabela

~~~python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fast_zero.models import User, table_registry


def test_create_user():
    engine = create_engine("sqlite:///:memory:")

    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            username="alice", password="secret", email="teste@test"
        )

        session.add(user)
        session.commit()
        session.refresh(user)

    assert user.id == 1
~~~

### Observações:

1. **`create_engine("sqlite:///:memory:")`**  
   - Cria o banco de dados na memória. Assim que o processo termina, ele é apagado.

2. **`table_registry.metadata.create_all(engine)`**  
   - Cria as tabelas do banco de dados com base no mapeamento definido no arquivo `model.py`.

3. **`with Session(engine) as session:`**
   - Inicia uma sessão para interação com o banco.
   - Essa sessão gerencia operações como inserir, consultar, atualizar e excluir registros.
   - O uso do `with` garante que a sessão será fechada automaticamente ao final do bloco.

4. **`add` e `commit`**  
   - Funcionam como no Git: você adiciona uma alteração e depois a confirma.

5. **`refresh`**  
   - Atualiza o objeto Python com os dados gerados pelo banco, como o ID automaticamente criado.

---

## Refatorando o Teste do Código

Vamos refatorar o teste para torná-lo mais organizado:

~~~python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fast_zero.app import app
from fast_zero.models import table_registry


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)
~~~

Agora podemos testar a criação de usuários:
~~~python
from sqlalchemy import select

from fast_zero.models import User


def test_create_user(session):
    new_user = User(username="alice", password="secret", email="teste@test")
    session.add(new_user)
    session.commit()

    user = session.scalar(select(User).where(User.username == "alice"))

    assert user.username == "alice"
~~~

---

# Configurando o Pydantic

### Instalando
~~~bash
poetry add pydantic-settings
~~~

### Configuração do `.env`

Crie o arquivo `.env`:
~~~
DATABASE_URL="sqlite:///database.db"
~~~

Ignore o arquivo de banco no repositório:
~~~bash
echo 'database.db' >> .gitignore
~~~

---

## Configurando o Alembic

### Instalando
~~~bash
poetry add alembic
~~~

### Inicializando
Ative o ambiente virtual e execute:
~~~bash
alembic init migrations
~~~

Se o nome do diretório for errado, apague-o e o arquivo `alembic.ini` antes de repetir o comando.

### Configurando o `env.py`

Dentro de `migrations/env.py`, modifique e adicione:
~~~python
from fast_zero.models import table_registry
from fast_zero.settings import Settings
 
config = context.config

config.set_main_option('sqlalchemy.url', Settings().DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = table_registry.metadata
~~~

### Gerando a Migração

Crie a migração:
~~~bash
alembic revision --autogenerate -m "create users table"
~~~

Verifique se o arquivo gerado em `migrations/versions/` está correto.

---

### Aplicando a Migração

Execute:
~~~bash
alembic upgrade head
~~~

---

# Exercícios

1. **Adicione o campo `updated_at` ao modelo `User`:**
   - Tipo: `datetime`
   - Não inicializável (`init=False`)
   - Atualizado automaticamente ao modificar o registro (`onupdate=func.now()`).

Resposta:
~~~python
updated_at: Mapped[datetime] = mapped_column(
    init=False, server_default=func.now(), onupdate=func.now()
)
~~~

2. **Crie uma nova migração:**
~~~bash
alembic revision --autogenerate -m "exercicio 02 aula 04"
~~~

3. **Aplique a migração ao banco de dados:**
~~~bash
alembic upgrade head
~~~

