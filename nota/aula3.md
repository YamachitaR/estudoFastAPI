Na aula passada estavamos falando sobre  **Pydantic**, vamos retorna ao tema 




# Endpoint  

Vamos criar **endpoint** para `users`


## Método `post`

Vale resaltar que o metódo `post`, seria para **postar**


No `app.py`, acrescenta 
~~~ python 
@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema):
    return user

~~~ 

**obs:** 
- `status_code=HTTPStatus.CREATED` vai ser **201**, pois **CREATED**
-  Repare no **response_model=UserPublic**, vamos explicar melhor no proximo passo. 


No `schemas.py`, acrescenta 

~~~ python 
from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    username: str
    email: EmailStr

~~~ 

**Observação**:
- Estamos criando dois "banco de dados", estamos fazendo isso porque queremos que `return user` do `app.py` retorne menos o `password`, para ver o resultado  que mostre a senha, mude o `response_model=UserPublic` para `response_model=UserSchema` 
- O email é uma `string` porém existe especial que verifica se a formatação esta correto. 


### Testando que foi feito até o momento 

Rode

~~~ bash 
task run
~~~ 

No navegador http://localhost:8000/docs 

Lá dentro, podemos testar. É fácil de testar.  


## Criando Banco de dado falso 

A ideia é mais para o lado de didático que operacional. 


Criamos e alteramos 
~~~ python 
class UserPublic(BaseModel):
    id:  int 
    username: str
    email: EmailStr

class UserDB(UserSchema):
    id:  int
~~~ 


**Observação** Eu acredito que como é um banco de dados hipotetico nos não vamos salvar a senha por causa desse motivo 


~~~python 

database = []  


@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema):
    user_with_id = UserDB(**user.model_dump(), id=len(database) + 1)  



    database.append(user_with_id)

    return user_with_id

~~~

Observação:

- `model_dump` vai servir para converter objeto em um dicionario 

### Testando essa modificação 

É o mesmo que do anterior, só que precisamos enviar mais de um, e ver se realmente esta mudando o **id**. Mas desse jeito manual é chato.

No `test_app.py`

~~~ python
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
~~~
 
 para rodar 

 ~~~
task test
 ~~~

 O código não está legal pois estamos repetindo o `client = TestClient(app)`


 ~~~ python 
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
~~~


## Crinado o método `Get`

Vale lembrar que o metódo `GET` seria pegar 


no `schemas.py `vamos acrescentar: 
~~~ python 
class UserList(BaseModel):
    users: list[UserPublic]
~~~ 

O **list** como o nome já diz vai lista todos. 



No `app.py` temos:
~~~ python 
from fast_zero.schemas import Message, UserDB, UserList, UserPublic, UserSchema

# código omitido

@app.get('/users/', response_model=UserList)
def read_users():
    return {'users': database}
~~~


### Testando nosso código 

Para nós testamos manualmente no navegador, para vale lembrar que **precisamos alimentetar o banco de dados primeiro, para depois testar o metódo get**



Ou podmeos, criar nosso teste automatizado:

~~~python 
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

~~~

**Uma pequena observação**: O certo o teste ser mais isoloado possivel, ou seja, no nosso caso estamos precisando que seja feito post para depois nos usamos get isso esta errado