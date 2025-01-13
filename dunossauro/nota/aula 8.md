# Fatory Boy 

A ideia seria criar um banco de dados, para que possamos utilizar para fazer teste. 

~~~ bash
poetry add --group dev factory-boy
~~~


Para criamos o banco de dados, 


~~~ python 
import factory

# ...

class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
~~~

após isso ele implementou no teste


~~~ python 

def test_update_user_with_wrong_user(client, other_user, token):
    response = client.put(
        f"/users/{other_user.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "mynewpassword",
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}


def test_delete_user_wrong_user(client, other_user, token):
    response = client.delete(
        f"/users/{other_user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Not enough permissions"}

~~~ 

Básicamente, estamos testando quando um usuário tenta fazer algo que é de outro usuário, tanto para `put` mudar e `del`.


# Parando o tempo

Agora queremos testa a validade do token, para isso precisamos ter o coantrole do tempo. Vamos utlizar a bilbioteca `freeze`

~~~  bash 
poetry add --group dev freezegun
~~~ 

No arquivo `test_users.py`

~~~ python 
from freezegun import freeze_time

# ...

def test_token_expired_after_time(client, user):
    with freeze_time('2023-07-14 12:00:00'): # paramos tempo nessa data
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password}, # criamos nosso token 
        )
        assert response.status_code == HTTPStatus.OK # verificando se criou corretamente
        token = response.json()['access_token'] # verificamos se criou corretamente 

    with freeze_time('2023-07-14 12:31:00'): # avançamos o tempo para essa data.
        response = client.put( # usamos put mas poderia ser o DEL
            f'/users/{user.id}',
            headers={'Authorization': f'Bearer {token}'}, 
            json={
                'username': 'wrongwrong',
                'email': 'wrong@wrong.com',
                'password': 'wrong',
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED # vericando erro de não autolizado 
        assert response.json() == {'detail': 'Could not validate credentials'}
~~~

Ao rodar o teste vai dá erro, pois ainda não fizemos a tratativa quando passar a valisade da crentencial 


~~~ python 
from jwt import DecodeError, ExpiredSignatureError, decode, encode

def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get('sub')
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except DecodeError:
        raise credentials_exception
    except ExpiredSignatureError: # Alteramos
        raise credentials_exception # Alteramos 

    user = session.scalar(
        select(User).where(User.email == token_data.username)
    )

    if not user:
        raise credentials_exception

    return user
~~~ 

## Testando quando usuário não existe

A ideia é manda um email (email é o login) que não existe no banco de dado 

~~~ python 
def test_token_inexistent_user(client):
    response = client.post(
        '/auth/token',
        data={'username': 'no_user@no_domain.com', 'password': 'testtest'},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Incorrect email or password'}

~~~


## Eviando usuarío que existe, mas a senha é incorreto 

~~~ python 
def test_token_wrong_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'wrong_password'}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {'detail': 'Incorrect email or password'}
~~~


# Refresh do token 

É uma boa prática e também é mais seguro.  Uma forma de mapear o usuário e assim caso tiver compoetamento suspeito é possivel agir. 

`auth.py`

~~~ python 
from fast_zero.security import (
    create_access_token,
    get_current_user,
    verify_password,
)

# ...

@router.post('/refresh_token', response_model=Token)
def refresh_access_token(
    user: User = Depends(get_current_user),
):
    new_access_token = create_access_token(data={'sub': user.email})

    return {'access_token': new_access_token, 'token_type': 'bearer'}

~~~ 


Também é necessário que façamos o teste:


Verifica se ele esta fazendo o refresh 
~~~ python 
def test_refresh_token(client, user, token):
    response = client.post(
        '/auth/refresh_token',
        headers={'Authorization': f'Bearer {token}'},
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'
~~~ 


Agora vamos verificar a expiração do token: 

~~~python
def test_token_expired_dont_refresh(client, user):
    with freeze_time('2023-07-14 12:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2023-07-14 12:31:00'):
        response = client.post(
            '/auth/refresh_token',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}
~~~