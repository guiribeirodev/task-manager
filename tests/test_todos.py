from datetime import datetime
from http import HTTPStatus

import factory.fuzzy
import pytest
from sqlalchemy.exc import DataError

from fast_zero.models import RecurrencePeriod, Todo, TodoState

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
        'user_id': None,
        'recurrence': 'none',
        'recurrence_days': None,
        'due_date': None,
        'created_at': time.isoformat(),
        'updated_at': time.isoformat(),
    }


class TodoFactory(factory.Factory):
    class Meta:
        model = Todo

    title = factory.Faker('text')
    description = factory.Faker('text')
    state = factory.fuzzy.FuzzyChoice(TodoState)
    recurrence = RecurrencePeriod.none
    recurrence_days = None
    due_date = None


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
async def test_list_todos_filter_recurrence(session, client):
    session.add_all(
        TodoFactory.create_batch(3, recurrence=RecurrencePeriod.daily)
    )
    session.add_all(
        TodoFactory.create_batch(2, recurrence=RecurrencePeriod.weekly)
    )
    await session.commit()

    response = client.get('/todos/?recurrence=daily')
    assert len(response.json()['todos']) == 3

    response_weekly = client.get('/todos/?recurrence=weekly')
    assert len(response_weekly.json()['todos']) == 2


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
async def test_patch_todo_recurring_daily_creates_next_instance(
    session, client
):
    todo = TodoFactory(
        state=TodoState.todo,
        recurrence=RecurrencePeriod.daily,
        due_date=datetime(2026, 8, 10, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    response = client.patch(
        f'/todos/{todo.id}',
        json={'state': 'done'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['state'] == 'done'

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 2

    done_task = [t for t in todos if t['id'] == todo.id][0]
    assert done_task['state'] == 'done'

    new_task = [t for t in todos if t['id'] != todo.id][0]
    assert new_task['state'] == 'todo'
    assert new_task['recurrence'] == 'daily'
    assert '2026-08-11' in new_task['due_date']


@pytest.mark.asyncio
async def test_patch_todo_recurring_weekly_creates_next_instance(
    session, client
):
    todo = TodoFactory(
        state=TodoState.todo,
        recurrence=RecurrencePeriod.weekly,
        due_date=datetime(2026, 8, 10, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    response = client.patch(
        f'/todos/{todo.id}',
        json={'state': 'done'},
    )
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 2

    new_task = [t for t in todos if t['id'] != todo.id][0]
    assert new_task['state'] == 'todo'
    assert new_task['recurrence'] == 'weekly'
    assert '2026-08-17' in new_task['due_date']


@pytest.mark.asyncio
async def test_patch_todo_recurring_monthly_creates_next_instance(
    session, client
):
    todo = TodoFactory(
        state=TodoState.todo,
        recurrence=RecurrencePeriod.monthly,
        due_date=datetime(2026, 8, 10, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    response = client.patch(
        f'/todos/{todo.id}',
        json={'state': 'done'},
    )
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 2

    new_task = [t for t in todos if t['id'] != todo.id][0]
    assert new_task['state'] == 'todo'
    assert new_task['recurrence'] == 'monthly'
    assert '2026-09-10' in new_task['due_date']


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
            'user_id': todo.user_id,
            'recurrence': todo.recurrence.value,
            'recurrence_days': todo.recurrence_days,
            'due_date': todo.due_date,
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


@pytest.mark.asyncio
async def test_create_todo_with_recurrence_days_weekly(client):
    response = client.post(
        '/todos/',
        json={
            'title': 'Academia',
            'description': 'Treino semanal',
            'state': 'todo',
            'recurrence': 'weekly',
            'recurrence_days': [0, 3, 4],
            'due_date': '2026-08-10T10:00:00',
        },
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['recurrence'] == 'weekly'
    assert data['recurrence_days'] == [0, 3, 4]


@pytest.mark.asyncio
async def test_patch_todo_recurring_weekly_with_days_cycles_correctly(
    session, client
):
    # Segunda-feira, 10 de Agosto de 2026 (weekday=0)
    todo = TodoFactory(
        title='Treino',
        state=TodoState.todo,
        recurrence=RecurrencePeriod.weekly,
        recurrence_days=[0, 3, 4],  # Seg, Qui, Sex
        due_date=datetime(2026, 8, 10, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    # 1. Conclui segunda -> deve criar para quinta (2026-08-13)
    response = client.patch(f'/todos/{todo.id}', json={'state': 'done'})
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 2
    task_thu = [t for t in todos if t['id'] != todo.id][0]
    assert task_thu['state'] == 'todo'
    assert task_thu['recurrence_days'] == [0, 3, 4]
    assert '2026-08-13' in task_thu['due_date']

    # 2. Conclui quinta -> deve criar para sexta (2026-08-14)
    response = client.patch(
        f'/todos/{task_thu["id"]}', json={'state': 'done'}
    )
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 3
    task_fri = [
        t for t in todos if t['id'] not in {todo.id, task_thu['id']}
    ][0]
    assert task_fri['state'] == 'todo'
    assert task_fri['recurrence_days'] == [0, 3, 4]
    assert '2026-08-14' in task_fri['due_date']

    # 3. Conclui sexta -> deve criar para a próxima segunda (2026-08-17)
    response = client.patch(
        f'/todos/{task_fri["id"]}', json={'state': 'done'}
    )
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 4
    task_next_mon = [
        t
        for t in todos
        if t['id'] not in {todo.id, task_thu['id'], task_fri['id']}
    ][0]
    assert task_next_mon['state'] == 'todo'
    assert task_next_mon['recurrence_days'] == [0, 3, 4]
    assert '2026-08-17' in task_next_mon['due_date']


@pytest.mark.asyncio
async def test_patch_todo_recurring_monthly_with_specific_day(session, client):
    # Todo dia 12 do mês
    todo = TodoFactory(
        title='Aluguel',
        state=TodoState.todo,
        recurrence=RecurrencePeriod.monthly,
        recurrence_days=[12],
        due_date=datetime(2026, 8, 12, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    response = client.patch(f'/todos/{todo.id}', json={'state': 'done'})
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 2
    next_task = [t for t in todos if t['id'] != todo.id][0]
    assert next_task['state'] == 'todo'
    assert next_task['recurrence_days'] == [12]
    assert '2026-09-12' in next_task['due_date']


@pytest.mark.asyncio
async def test_patch_todo_recurring_monthly_with_multiple_days(
    session, client
):
    # Dias 5 e 20 de cada mês
    todo = TodoFactory(
        title='Relatório Quinzenal',
        state=TodoState.todo,
        recurrence=RecurrencePeriod.monthly,
        recurrence_days=[5, 20],
        due_date=datetime(2026, 8, 5, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    # 1. Conclui dia 5 -> deve criar para dia 20 do mesmo mês (2026-08-20)
    response = client.patch(f'/todos/{todo.id}', json={'state': 'done'})
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 2
    task_20th = [t for t in todos if t['id'] != todo.id][0]
    assert '2026-08-20' in task_20th['due_date']

    # 2. Conclui dia 20 -> deve criar para dia 5 do mês seguinte (2026-09-05)
    response = client.patch(
        f'/todos/{task_20th["id"]}', json={'state': 'done'}
    )
    assert response.status_code == HTTPStatus.OK

    todos_resp = client.get('/todos/')
    todos = todos_resp.json()['todos']
    assert len(todos) == 3
    task_next_month_5th = [
        t for t in todos if t['id'] not in {todo.id, task_20th['id']}
    ][0]
    assert '2026-09-05' in task_next_month_5th['due_date']


def test_create_todo_invalid_recurrence_days_weekly(client):
    response = client.post(
        '/todos/',
        json={
            'title': 'Inválido',
            'description': 'Dia inválido',
            'state': 'todo',
            'recurrence': 'weekly',
            'recurrence_days': [7],
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_todo_invalid_recurrence_days_monthly(client):
    response = client.post(
        '/todos/',
        json={
            'title': 'Inválido',
            'description': 'Dia inválido',
            'state': 'todo',
            'recurrence': 'monthly',
            'recurrence_days': [32],
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_schedule_empty(client):
    response = client.get('/todos/schedule?date=2026-08-25')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'date': '2026-08-25',
        'todos': [],
    }


def test_get_schedule_default_date(client):
    response = client.get('/todos/schedule')
    assert response.status_code == HTTPStatus.OK
    assert 'date' in response.json()
    assert isinstance(response.json()['todos'], list)


@pytest.mark.asyncio
async def test_get_schedule_with_direct_due_date_task(session, client):
    todo = TodoFactory(
        title='Tarefa Pontual',
        state=TodoState.todo,
        due_date=datetime(2026, 8, 25, 14, 0, 0),
        recurrence=RecurrencePeriod.none,
    )
    session.add(todo)
    await session.commit()

    # Data correta
    resp_match = client.get('/todos/schedule?date=2026-08-25')
    assert resp_match.status_code == HTTPStatus.OK
    todos_match = resp_match.json()['todos']
    assert len(todos_match) == 1
    assert todos_match[0]['title'] == 'Tarefa Pontual'
    assert todos_match[0]['is_recurring_occurrence'] is False

    # Outra data
    resp_other = client.get('/todos/schedule?date=2026-08-26')
    assert resp_other.status_code == HTTPStatus.OK
    assert len(resp_other.json()['todos']) == 0


@pytest.mark.asyncio
async def test_get_schedule_with_weekly_recurring_days(session, client):
    # Segunda-feira, 10 de Agosto de 2026
    todo = TodoFactory(
        title='Treino Semanal',
        state=TodoState.todo,
        recurrence=RecurrencePeriod.weekly,
        recurrence_days=[0, 3, 4],  # Seg, Qui, Sex
        due_date=datetime(2026, 8, 10, 10, 0, 0),
    )
    session.add(todo)
    await session.commit()

    # Segunda (2026-08-10) -> instância direta
    resp_mon = client.get('/todos/schedule?date=2026-08-10')
    todos_mon = resp_mon.json()['todos']
    assert len(todos_mon) == 1
    assert todos_mon[0]['is_recurring_occurrence'] is False

    # Terça (2026-08-11) -> não ocorre
    resp_tue = client.get('/todos/schedule?date=2026-08-11')
    assert len(resp_tue.json()['todos']) == 0

    # Quinta (2026-08-13) -> ocorrência projetada
    resp_thu = client.get('/todos/schedule?date=2026-08-13')
    todos_thu = resp_thu.json()['todos']
    assert len(todos_thu) == 1
    assert todos_thu[0]['is_recurring_occurrence'] is True
    assert '2026-08-13T10:00:00' in todos_thu[0]['due_date']

    # Próxima Segunda (2026-08-17) -> ocorrência projetada
    resp_next_mon = client.get('/todos/schedule?date=2026-08-17')
    todos_next_mon = resp_next_mon.json()['todos']
    assert len(todos_next_mon) == 1
    assert todos_next_mon[0]['is_recurring_occurrence'] is True


@pytest.mark.asyncio
async def test_get_schedule_with_monthly_recurring_day(session, client):
    todo = TodoFactory(
        title='Pagar Aluguel',
        state=TodoState.todo,
        recurrence=RecurrencePeriod.monthly,
        recurrence_days=[12],
        due_date=datetime(2026, 8, 12, 9, 0, 0),
    )
    session.add(todo)
    await session.commit()

    # Mês base (2026-08-12)
    resp_aug = client.get('/todos/schedule?date=2026-08-12')
    todos_aug = resp_aug.json()['todos']
    assert len(todos_aug) == 1
    assert todos_aug[0]['is_recurring_occurrence'] is False

    # Mês seguinte (2026-09-12)
    resp_sep = client.get('/todos/schedule?date=2026-09-12')
    todos_sep = resp_sep.json()['todos']
    assert len(todos_sep) == 1
    assert todos_sep[0]['is_recurring_occurrence'] is True
    assert '2026-09-12T09:00:00' in todos_sep[0]['due_date']

    # Dia diferente (2026-09-13)
    resp_diff = client.get('/todos/schedule?date=2026-09-13')
    assert len(resp_diff.json()['todos']) == 0


@pytest.mark.asyncio
async def test_get_schedule_with_daily_recurrence(session, client):
    todo = TodoFactory(
        title='Leitura Diária',
        state=TodoState.todo,
        recurrence=RecurrencePeriod.daily,
        due_date=datetime(2026, 8, 10, 8, 0, 0),
    )
    session.add(todo)
    await session.commit()

    # Futuro (2026-08-15)
    resp_future = client.get('/todos/schedule?date=2026-08-15')
    todos_future = resp_future.json()['todos']
    assert len(todos_future) == 1
    assert todos_future[0]['is_recurring_occurrence'] is True

    # Passado antes do base_date (2026-08-05)
    resp_past = client.get('/todos/schedule?date=2026-08-05')
    assert len(resp_past.json()['todos']) == 0


@pytest.mark.asyncio
async def test_get_schedule_filters_by_telegram_id(
    session, client, user, other_user
):
    todo_user_1 = TodoFactory(
        title='Tarefa User 1',
        state=TodoState.todo,
        user_id=user.id,
        due_date=datetime(2026, 8, 10, 10, 0, 0),
        recurrence=RecurrencePeriod.daily,
    )
    todo_user_2 = TodoFactory(
        title='Tarefa User 2',
        state=TodoState.todo,
        user_id=other_user.id,
        due_date=datetime(2026, 8, 10, 10, 0, 0),
        recurrence=RecurrencePeriod.daily,
    )
    session.add_all([todo_user_1, todo_user_2])
    await session.commit()

    resp_u1 = client.get(
        f'/todos/schedule?date=2026-08-12&telegram_id={user.id}'
    )
    todos_u1 = resp_u1.json()['todos']
    assert len(todos_u1) == 1
    assert todos_u1[0]['title'] == 'Tarefa User 1'

    resp_u2 = client.get(
        f'/todos/schedule?date=2026-08-12&telegram_id={other_user.id}'
    )
    todos_u2 = resp_u2.json()['todos']
    assert len(todos_u2) == 1
    assert todos_u2[0]['title'] == 'Tarefa User 2'
