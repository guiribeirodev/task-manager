from http import HTTPStatus


def test_root_deve_retornar_ok_e_ola_mundo(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá Mundo!'}


def test_exercicio_ola_mundo_em_html(client):
    response = client.get('/exercicio-html')

    assert response.status_code == HTTPStatus.OK
    assert '<h1> Olá Mundo </h1>' in response.text


def test_create_user_should_return_409_username_exists__exercicio(
    client, user
):
    response = client.post(
        '/users/',
        json={
            'username': user.username,
            'email': 'alice@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username already exists'}


def test_create_user_should_return_409_email_exists__exercicio(client, user):
    response = client.post(
        '/users/',
        json={
            'username': 'alice',
            'email': user.email,
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Email already exists'}


def test_get_user___exercicio(client, user):
    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': user.username,
        'email': user.email,
        'id': user.id,
    }


def test_get_user_should_return_not_found__exercicio(client):
    response = client.get('/users/666')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


# def test_get_current_user_not_found__exercicio(client):
#     data = {'no-email': 'test'}
#     token = create_access_token(data)

#     response = client.delete(
#         '/users/1',
#         headers={'Authorization': f'Bearer {token}'},
#     )

#     assert response.status_code == HTTPStatus.UNAUTHORIZED
#     assert response.json() == {'detail': 'Could not validate credentials'}


# def test_get_current_user_does_not_exists__exercicio(client):
#     data = {'sub': 'test@test'}
#     token = create_access_token(data)

#     response = client.delete(
#         '/users/1',
#         headers={'Authorization': f'Bearer {token}'},
#     )

#     assert response.status_code == HTTPStatus.UNAUTHORIZED
#     assert response.json() == {'detail': 'Could not validate credentials'}
