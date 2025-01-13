
# Vamos conectar ao Banco de Dados

## No método `Post`

### Modificando

```python
# Verificar se precisa de mais bibliotecas
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema):
    # Estudar para entender melhor
    engine = create_engine(Settings().DATABASE_URL)
    session = Session(engine)

    # Verificando se já existe email ou nome
    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    # Só entra aqui se o nome ou email já estiverem cadastrados
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Username already exists',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Email already exists',
            )

    # Criando o usuário para inserir no banco de dados
    db_user = User(
        username=user.username, password=user.password, email=user.email
    )

    session.add(db_user)  # Similar ao GitHub
    session.commit()  # Similar ao GitHub
    session.refresh(db_user)  # Atualizar a tabela

    return db_user
```

Para verificar se realmente gravou, utilize um programa específico para acessar o arquivo `database.db`.

---

## Refatorando o código

O trecho:

```python
engine = create_engine(Settings().DATABASE_URL)
session = Session(engine)
```

será utilizado várias vezes. Por isso, vamos criar o arquivo `fast_zero/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fast_zero.settings import Settings

engine = create_engine(Settings().DATABASE_URL)

def get_session():  # pragma: no cover (ignora o teste deste trecho)
    with Session(engine) as session:
        yield session
```

Agora, nossa função será refatorada:

### Observação:

- **`# pragma: no cover`**: utilizado para que os testes ignorem este trecho de código.
- Como estamos utilizando `yield`, precisaremos usar `Depends` no arquivo `app.py`.

```python
# Verificar as bibliotecas necessárias para rodar o programa

@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session = Depends(get_session)):
    # Pesquise mais sobre Depends
    # Em resumo, usamos devido ao uso de yield na função get_session
    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    # Daqui para baixo, é semelhante ao que já fizemos
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Username already exists',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Email already exists',
            )

    db_user = User(
        username=user.username, password=user.password, email=user.email
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user
```

---

## Conflito ao trocar o banco de dados

Ao realizar testes, precisamos trocar o banco de dados. Durante essa troca, ocorre um conflito com threads, pois cada função de teste cria uma thread. O conflito ocorre porque o banco de teste precisa estar na mesma thread.

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fast_zero.app import app
from fast_zero.database import get_session
from fast_zero.models import table_registry

@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def session():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)
```

Ao rodar o teste, ele não passará até ajustarmos.


## Modificando o método `GET`

```python
@app.get('/users/', response_model=UserList)
def read_users(
    skip: int = 0, limit: int = 100, session: Session = Depends(get_session)
):
    users = session.scalars(select(User).offset(skip).limit(limit)).all()
    return {'users': users}
```

### Observações:

- `skip` e `offset` indicam a **posição inicial** a partir da qual queremos que os valores sejam retornados.
- `limit` e `limit(limit)).all()` indicam a **quantidade máxima** de valores que queremos retornar.
- `Depends(get_session)` já foi discutido anteriormente.

---

### Teste

Este teste verifica o comportamento quando **não há nenhum usuário** no banco de dados:

```python
def test_read_users(client):
    response = client.get('/users')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}
```

Agora vamos criar um banco de dados com usuários para realizar testes com dados reais:

```python
from fast_zero.models import User, table_registry


@pytest.fixture
def user(session):
    user = User(username='Teste', email='teste@test.com', password='testtest')
    session.add(user)
    session.commit()
    session.refresh(user)

    return user
```

Agora podemos testar com um usuário já presente no banco de dados:

```python
from fast_zero.schemas import UserPublic

def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()  # Obtendo dados do banco
    response = client.get('/users/')  # Obtendo dados da API
    assert response.json() == {'users': [user_schema]}
```

---

## Integrando ORM com Pydantic

Para realizar a integração, utilizamos a configuração `model_config = ConfigDict(from_attributes=True)`:

```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
```

---

## Modificando o `PUT`

```python
@app.put('/users/{user_id}', response_model=UserPublic)
def update_user(
    user_id: int, user: UserSchema, session: Session = Depends(get_session)
):
    db_user = session.scalar(select(User).where(User.id == user_id))
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    try:
        db_user.username = user.username
        db_user.password = user.password
        db_user.email = user.email
        session.commit()
        session.refresh(db_user)

        return db_user

    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Username or Email already exists'
        )
```

### Observação:

Estamos utilizando **tratamento de exceção** devido às regras de negócio configuradas no banco de dados.

---

### Teste para `PUT`

Este teste verifica a atualização de um usuário existente:

```python
def test_update_user(client, user):
    response = client.put(
        '/users/1',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': 1,
    }
```

---

### Teste para conflitos de integridade

```python
def test_update_integrity_error(client, user):
    # Inserindo o usuário "fausto"
    client.post(
        "/users",
        json={
            "username": "fausto",
            "email": "fausto@example.com",
            "password": "secret",
        },
    )

    # Tentando alterar o usuário das fixtures para "fausto"
    response_update = client.put(
        f"/users/{user.id}",
        json={
            "username": "fausto",
            "email": "bob@example.com",
            "password": "mynewpassword",
        },
    )
    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        "detail": "Username or Email already exists"
    }
```

---

## Modificando o `DELETE`

```python
@app.delete('/users/{user_id}', response_model=Message)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    db_user = session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    session.delete(db_user)
    session.commit()

    return {'message': 'User deleted'}
```

### Teste para `DELETE`

```python
def test_delete_user(client, user):
    response = client.delete('/users/1')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}
```

---

# Exercícios

1. Escreva um teste para o endpoint `POST` (`create_user`) validando o erro 400 quando o username já está registrado:

```python
def test_post_create_user_exists(client, user):
    response = client.post(
        "/users",
        json={
            "username": "Teste",
            "email": "alice@example.com",
            "password": "secret",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {"detail": "Username already exists"}
```

2. Escreva um teste similar ao exercício anterior, mas para o caso de e-mail já registrado.
    
3. Atualize os testes para incluir suporte ao banco de dados:
    
    a. Escreva um teste para erro 404 no endpoint `PUT`:
    
    ```python
    def test_update_user_wrong_index(client, user):
        response = client.put(
            "/users/99",
            json={
                "username": "bob",
                "email": "bob@example.com",
                "password": "mynewpassword",
            },
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "User not found"}
    ```
    
    b. Escreva um teste para erro 404 no endpoint `DELETE`:
    
    ```python
    def test_delete_index_not_exist(client, user):
        response = client.delete("/users/99")
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "User not found"}
    ```
    
4. Implemente o endpoint de listagem por ID e escreva os testes para casos de sucesso (`200`) e erro (`404`):

~~~ python 
@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, session: Session = Depends(get_session)):
    db_user = session.scalar(select(User).where(User.id == user_id))
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return db_user
~~~




Sucesso:
    
~~~ python
    def test_read_only_user(client, user):
        response = client.get(f"/users/{user.id}")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "username": user.username,
            "email": user.email,
            "id": user.id,
        }
~~~
    
Erro:
    
```python
    def test_read_only_user_wrong(client, user):
        response = client.get(f"/users/{user.id + 1}")
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "User not found"}
    ```
