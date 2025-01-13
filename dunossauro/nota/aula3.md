
Na aula passada, estávamos falando sobre **Pydantic**. Vamos retornar ao tema.


# Endpoint  

Vamos criar um **endpoint** para `users`.

## Método `POST`

Vale ressaltar que o método `POST` é utilizado para **postar**.

No arquivo `app.py`, acrescente o seguinte:

```python
@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema):
    return user
```

**Obs.:** 
- `status_code=HTTPStatus.CREATED` significa **201**, pois indica que o recurso foi **CRIADO**.
- Repare no uso de **`response_model=UserPublic`**, que será explicado melhor no próximo passo.

No arquivo `schemas.py`, acrescente:

```python
from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    username: str
    email: EmailStr
```

**Observação**:
- Estamos criando dois esquemas para "bancos de dados". Fazemos isso porque queremos que o `return user` do `app.py` **não inclua a senha**. Caso queira que o retorno inclua a senha, basta alterar `response_model=UserPublic` para `response_model=UserSchema`. 
- O campo `email` é uma `string`, mas estamos utilizando `EmailStr`, que verifica se o formato do e-mail está correto.

---

### Testando o que foi feito até agora 

Rode o seguinte comando:

```bash
task run
```

Acesse no navegador: [http://localhost:8000/docs](http://localhost:8000/docs)

Lá, você poderá testar facilmente.

---

## Criando um Banco de Dados Falso 

A ideia aqui é didática, não operacional.

Altere o código no `schemas.py`:

```python
class UserPublic(BaseModel):
    id: int 
    username: str
    email: EmailStr

class UserDB(UserSchema):
    id: int
```

**Observação:** Como se trata de um banco de dados fictício, decidimos **não salvar a senha**.

No arquivo `app.py`, altere:

```python
database = []  

@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema):
    user_with_id = UserDB(**user.model_dump(), id=len(database) + 1)  

    database.append(user_with_id)
    return user_with_id
```

**Observação**:
- O método `model_dump()` converte o objeto em um dicionário.

---

### Testando as modificações 

Faça o mesmo teste manual anterior, mas envie mais de um usuário para verificar se o **ID** está sendo incrementado corretamente. Para evitar testes manuais repetitivos, automatize os testes:

No arquivo `test_app.py`, crie:

```python
def test_create_user():
    client = TestClient(app)

    response = client.post(
        "/users/",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "secret",
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        "username": "alice",
        "email": "alice@example.com",
        "id": 1,
    }
```

Para rodar os testes:

```bash
task test
```

Como o código atual repete `client = TestClient(app)` em todos os testes, podemos refatorá-lo usando uma fixture:

No arquivo `test_app.py`:

```python
from http import HTTPStatus

def test_root_deve_retornar_ok_e_ola_mundo(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá Mundo!'}

def test_create_user(client):
    response = client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'alice',
        'email': 'alice@example.com',
        'id': 1,
    }
```

Crie um arquivo chamado `conftest.py` no diretório `test`:

```python
import pytest
from fastapi.testclient import TestClient

from fast_zero.app import app

@pytest.fixture
def client():
    return TestClient(app)
```

Esse trecho evita a replicação do código `client = TestClient(app)`.

---

## Criando o Método `GET`

O método `GET` é utilizado para **obter** informações.

No arquivo `schemas.py`, acrescente:

```python
class UserList(BaseModel):
    users: list[UserPublic]
```

No arquivo `app.py`, acrescente:

```python
from fast_zero.schemas import Message, UserDB, UserList, UserPublic, UserSchema

@app.get('/users/', response_model=UserList)
def read_users():
    return {'users': database}
```

---

### Testando o Método `GET` 

Para testar manualmente, primeiro insira dados no banco usando o método `POST` e, em seguida, use o método `GET`.

Para automatizar os testes:

```python
def test_read_users(client):
    response = client.get('/users/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'users': [
            {
                'username': 'alice',
                'email': 'alice@example.com',
                'id': 1,
            }
        ]
    }
```

**Observação:** Um teste ideal deve ser **isolado**. No exemplo acima, o teste depende do método `POST` para alimentar o banco antes de usar o `GET`, o que não é recomendado.



---

## Implementando o Método `PUT`

O método `PUT` é usado para atualizar. Vamos acrescentar o seguinte trecho de código no `app.py`:

~~~python
from fastapi import FastAPI, HTTPException

@app.put('/users/{user_id}', response_model=UserPublic)
def update_user(user_id: int, user: UserSchema):
    if user_id > len(database) or user_id < 1: 
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        ) 

    user_with_id = UserDB(**user.model_dump(), id=user_id)
    database[user_id - 1] = user_with_id 

    return user_with_id
~~~

- Retorna erro 404 caso o usuário não exista.  
- Para rodar, siga as instruções anteriores, mas lembre-se de que existe uma ordem a ser seguida para que tudo funcione corretamente.  

Como somos bons programadores, precisamos criar testes automatizados. O código abaixo está autoexplicativo:

~~~python
def test_update_user(client):
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
~~~

---

## Método `DEL`

Pelo nome, já esperamos que seja para `DELETE`:

~~~python
@app.delete('/users/{user_id}', response_model=Message)
def delete_user(user_id: int):
    if user_id > len(database) or user_id < 1:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    del database[user_id - 1]

    return {'message': 'User deleted'}
~~~

- Caso o `ID` fornecido não seja encontrado, retorna 404. Em caso de sucesso, retorna 200.  

Segue o teste para este método:

~~~python
def test_delete_user(client):
    response = client.delete('/users/1')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}
~~~

---

## Exercício

1. Escrever um teste para o erro **404 (NOT FOUND)** no endpoint de `PUT`:

~~~python
def test_update_user_error(client):
    response = client.put(
        "/users/3",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "mynewpassword",
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "User not found"}
~~~

---

2. Escrever um teste para o erro **404 (NOT FOUND)** no endpoint de `DELETE`:

~~~python
def test_delete_user_error(client):
    response = client.delete("/users/6")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "User not found"}
~~~

---

3. Criar um endpoint `GET` para buscar um único recurso (`users/{id}`) e escrever os testes para os casos de sucesso (`200`) e erro (`404`):

### Endpoint:
~~~python
@app.get("/users/{user_id}", response_model=UserPublic)
def read_users(user_id: int):
    if user_id > len(database) or user_id < 1:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return database[user_id - 1]
~~~

### Testes:
~~~python
def test_read_user(client):
    response = client.get("/users/1")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "username": "alice",
        "email": "alice@example.com",
        "id": 1,
    }

def test_read_user_error(client):
    response = client.get("/users/9999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {"detail": "User not found"}
~~~



