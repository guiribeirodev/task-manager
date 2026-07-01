from http import HTTPStatus

import factory.fuzzy
import pytest
from sqlalchemy.exc import DataError

from fast_zero.models import Todo, TodoState

# from tests.conftest import mock_db_time
# from tests.factories import TodoFactory


def test_create_todo(client, mock_db_time):
    with mock_db_time(model=Todo) as time:
        response = client.post(
            '/todos/',
            json={
                'title': 'Test todo',
                'description': 'Test todo description',
                'state': 'draft',
            },
        )

    assert response.json() == {
        'id': 1,
        'title': 'Test todo',
        'description': 'Test todo description',
        'state': 'draft',
        'created_at': time.isoformat(),
        'updated_at': time.isoformat(),
    }


class TodoFactory(factory.Factory):
    class Meta:
        model = Todo

    title = factory.Faker('text')
    description = factory.Faker('text')
    state = factory.fuzzy.FuzzyChoice(TodoState)


@pytest.mark.asyncio
async def test_list_todos_should_return_5_todos(session, client):
    expected_todos = 5
    session.add_all(TodoFactory.create_batch(5))
    await session.commit()

    response = client.get('/todos/')

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_pagination_should_return_2_todos(session, client):
    expected_todos = 2
    session.add_all(TodoFactory.create_batch(5))
    await session.commit()

    response = client.get('/todos/?offset=1&limit=2')

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_title_should_return_5_todos(session, client):
    expected_todos = 5
    session.add_all(TodoFactory.create_batch(5, title='Test todo 1'))
    await session.commit()

    response = client.get('/todos/?title=Test todo 1')

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_description_should_return_5_todos(
    session, client
):
    expected_todos = 5
    session.add_all(TodoFactory.create_batch(5, description='description'))
    await session.commit()

    response = client.get('/todos/?description=desc')

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_state_should_return_5_todos(session, client):
    expected_todos = 5
    session.add_all(TodoFactory.create_batch(5, state=TodoState.draft))
    await session.commit()

    response = client.get('/todos/?state=draft')

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_combined_should_return_5_todos(
    session, client
):
    expected_todos = 5
    session.add_all(
        TodoFactory.create_batch(
            5,
            title='Test todo combined',
            description='combined description',
            state=TodoState.done,
        )
    )

    session.add_all(
        TodoFactory.create_batch(
            3,
            title='Other title',
            description='other description',
            state=TodoState.todo,
        )
    )
    await session.commit()

    response = client.get(
        '/todos/?title=Test todo combined&description=combined&state=done'
    )

    assert len(response.json()['todos']) == expected_todos


def test_patch_todo_error(client):
    response = client.patch('/todos/10', json={})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


@pytest.mark.asyncio
async def test_patch_todo(session, client):
    todo = TodoFactory()

    session.add(todo)
    await session.commit()

    response = client.patch(
        f'/todos/{todo.id}',
        json={'title': 'teste!'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'teste!'


@pytest.mark.asyncio
async def test_delete_todo(session, client):
    todo = TodoFactory()

    session.add(todo)
    await session.commit()

    response = client.delete(f'/todos/{todo.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Task has been deleted successfully.'
    }


def test_delete_todo_error(client):
    response = client.delete(f'/todos/{10}')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


@pytest.mark.asyncio
async def test_list_todos_should_return_all_expected_fields__exercicio(
    session, client, mock_db_time
):
    with mock_db_time(model=Todo) as time:
        todo = TodoFactory.create()
        session.add(todo)
        await session.commit()

    await session.refresh(todo)
    response = client.get('/todos/')

    assert response.json()['todos'] == [
        {
            'created_at': time.isoformat(),
            'updated_at': time.isoformat(),
            'description': todo.description,
            'id': todo.id,
            'state': todo.state,
            'title': todo.title,
        }
    ]


@pytest.mark.asyncio
async def test_create_todo_error(session):
    todo = Todo(
        title='Test Todo',
        description='Test Desc',
        state='test',
    )

    session.add(todo)

    with pytest.raises(DataError):
        await session.commit()


def test_list_todos_filter_min_length_exercicio_06(client):
    tiny_string = 'a'
    response = client.get(f'/todos/?title={tiny_string}')

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_todos_filter_max_length_exercicio_06(client):
    large_string = 'a' * 22
    response = client.get(f'/todos/?title={large_string}')

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
