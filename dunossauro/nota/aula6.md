# Autenticação e Atualização

## Gerando tokens JWT

Como funciona o `JWT`? Basicamente, você envia seu `email` e `senha` para o servidor. Caso tudo esteja correto, o servidor retorna um token, que possui uma validade. Uma analogia: imagine que você vai à recepção de um hotel (representando o envio do email e senha), o atendente verifica suas informações e te dá uma chave (token) para acessar o hotel. Assim como o token, a chave não permite acesso a qualquer área e possui um prazo de validade.

Antes de mais nada, precisamos instalar:

~~~bash
poetry add pyjwt "pwdlib[argon2]"
~~~

Vamos criar o arquivo `security.py`, que conterá o seguinte:

~~~python
from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, decode, encode
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.schemas import TokenData


# Isso é provisório; posteriormente será colocado no .env
SECRET_KEY = 'your-secret-key'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = PasswordHash.recommended()

# Criação do token, com inclusão do tempo de expiração
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({'exp': expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função para criptografar a senha, retornando um hash
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Função para verificar se a senha está correta
# 1º argumento: senha em texto simples
# 2º argumento: hash gerado em get_password_hash
# Retorno: True se estiver correta, False caso contrário
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Não foi possível validar as credenciais',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except DecodeError:
        raise credentials_exception

    user = session.scalar(
        select(User).where(User.email == token_data.username)
    )

    if not user:
        raise credentials_exception

    return user
~~~

## Alterando `POST`

Queremos que, ao receber a senha, ela seja criptografada.

~~~python
from fast_zero.security import get_password_hash

...

@app.post('/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic)

...

hashed_password = get_password_hash(user.password)  # Adicionado

db_user = User(
    email=user.email,
    username=user.username,
    password=hashed_password,  # Modificado
)
~~~

## Modificando o método `PUT`

~~~python
@app.put('/users/{user_id}', response_model=UserPublic)
def update_user(
    user_id: int,
    user: UserSchema,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),  # Exige que esteja logado
):
    if current_user.id != user_id:  # Exige que seja o próprio usuário para realizar a operação
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissões insuficientes'
        )
    try:
        current_user.username = user.username
        current_user.password = get_password_hash(user.password)  # Criptografa a senha
        current_user.email = user.email
        session.commit()
        session.refresh(current_user)

        return current_user

    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Nome de usuário ou email já existem',
        )
~~~

No **DELETE**, também adicionaremos a restrição de que é necessário estar logado.

~~~python
@app.delete('/users/{user_id}', response_model=Message)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),  # Exige que esteja logado
):
    if current_user.id != user_id:  # Verifica se é o próprio usuário
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissões insuficientes'
        )

    session.delete(current_user)
    session.commit()

    return {'message': 'Usuário deletado'}
~~~

## Voltando ao token

Agora vamos gerar o token e criar o endpoint para login.

No `schemas.py`:

~~~python
class Token(BaseModel):
    access_token: str
    token_type: str
~~~

Vamos criar o **endpoint** para gerar o token:

~~~python
from fastapi.security import OAuth2PasswordRequestForm
from fast_zero.schemas import Token
from fast_zero.security import (
    create_access_token,
    verify_password,
)

@app.post('/token', response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session),
):
    user = session.scalar(select(User).where(User.email == form_data.username))

    if not user:  # Caso o usuário não exista
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Email ou senha incorretos'  # Não dê dicas sobre qual está incorreto
        )

    if not verify_password(form_data.password, user.password):  # Senha incorreta
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Email ou senha incorretos'  # Não dê dicas sobre qual está incorreto
        )

    access_token = create_access_token(data={'sub': user.email})  # Cria o token

    return {'access_token': access_token, 'token_type': 'bearer'}
~~~

Agora vamos testar o token:

~~~python
def test_get_token(client, user):
    response = client.post(
        '/token',
        data={'username': user.email, 'password': user.password},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'token_type' in token
~~~

Adicional no `schemas.py`:

~~~python
class TokenData(BaseModel):
    username: str | None = None
~~~