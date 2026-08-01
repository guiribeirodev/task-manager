from http import HTTPStatus

from fast_zero.schemas import UserPublic


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


def test_create_user_with_telegram_id(client):
    telegram_id = 6930770036
    response = client.post(
        '/users/',
        json={
            'id': telegram_id,
            'username': 'telegram_user',
            'email': 'telegram@example.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'telegram_user',
        'email': 'telegram@example.com',
        'id': telegram_id,
    }

    # Test duplicate Telegram ID
    response_dup = client.post(
        '/users/',
        json={
            'id': telegram_id,
            'username': 'other_user',
            'email': 'other@example.com',
            'password': 'secret',
        },
    )
    assert response_dup.status_code == HTTPStatus.CONFLICT
    assert response_dup.json() == {'detail': 'User already exists'}


def test_read_users(client):
    response = client.get('/users')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}


def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/')
    assert response.json() == {'users': [user_schema]}


def test_read_users_me_is_unavailable(client):
    response = client.get('/users/me')

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_user_is_unavailable(client, user):
    response = client.put(
        f'/users/{user.id}',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
        },
    )

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_delete_user_is_unavailable(client, user):
    response = client.delete(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
