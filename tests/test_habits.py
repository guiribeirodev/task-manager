from datetime import date, timedelta
from http import HTTPStatus

import factory
import pytest

from fastapi.testclient import TestClient

from fast_zero.app import app
from fast_zero.database import get_session
from fast_zero.models import Habit, RecurrencePeriod


class HabitFactory(factory.Factory):
    class Meta:
        model = Habit

    title = factory.Faker('sentence')
    description = factory.Faker('sentence')
    recurrence = RecurrencePeriod.daily
    recurrence_days = None
    is_active = True


def test_create_habit(client, mock_db_time):
    with mock_db_time(model=Habit) as time:
        response = client.post(
            '/habits/',
            json={
                'title': 'Oração',
                'description': '',
                'user_id': 6930770036,
                'recurrence': 'daily',
                'recurrence_days': None,
                'is_active': True,
            },
        )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'title': 'Oração',
        'description': '',
        'user_id': 6930770036,
        'recurrence': 'daily',
        'recurrence_days': None,
        'is_active': True,
        'created_at': time.isoformat(),
        'updated_at': time.isoformat(),
    }


def test_create_habit_default_values(client):
    response = client.post(
        '/habits/',
        json={'title': 'Leitura Diária'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['title'] == 'Leitura Diária'
    assert data['description'] == ''
    assert data['recurrence'] == 'daily'
    assert data['recurrence_days'] is None
    assert data['is_active'] is True
    assert data['user_id'] is None


def test_create_habit_invalid_weekly_recurrence(client):
    response = client.post(
        '/habits/',
        json={
            'title': 'Academia',
            'recurrence': 'weekly',
            'recurrence_days': [0, 7],  # 7 is invalid (must be 0-6)
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_habit_invalid_monthly_recurrence(client):
    response = client.post(
        '/habits/',
        json={
            'title': 'Pagar Contas',
            'recurrence': 'monthly',
            'recurrence_days': [0],  # 0 is invalid (must be 1-31)
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_habits_should_return_all_habits(session, client):
    expected_habits = 3
    session.add_all(HabitFactory.create_batch(3))
    await session.commit()

    response = client.get('/habits/')

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['habits']) == expected_habits


@pytest.mark.asyncio
async def test_list_habits_pagination(session, client):
    session.add_all(HabitFactory.create_batch(5))
    await session.commit()

    response = client.get('/habits/?offset=1&limit=2')

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()['habits']) == 2


@pytest.mark.asyncio
async def test_list_habits_filter_by_telegram_id(session, client):
    habit1 = HabitFactory.create(user_id=12345)
    habit2 = HabitFactory.create(user_id=67890)
    session.add_all([habit1, habit2])
    await session.commit()

    response = client.get('/habits/?telegram_id=12345')

    assert response.status_code == HTTPStatus.OK
    habits = response.json()['habits']
    assert len(habits) == 1
    assert habits[0]['user_id'] == 12345


@pytest.mark.asyncio
async def test_list_habits_filter_by_is_active(session, client):
    active_habit = HabitFactory.create(is_active=True)
    inactive_habit = HabitFactory.create(is_active=False)
    session.add_all([active_habit, inactive_habit])
    await session.commit()

    response = client.get('/habits/?is_active=false')

    assert response.status_code == HTTPStatus.OK
    habits = response.json()['habits']
    assert len(habits) == 1
    assert habits[0]['is_active'] is False


@pytest.mark.asyncio
async def test_list_habits_filter_by_title(session, client):
    habit = HabitFactory.create(title='Meditar')
    session.add(habit)
    await session.commit()

    response = client.get('/habits/?title=Medit')

    assert response.status_code == HTTPStatus.OK
    habits = response.json()['habits']
    assert len(habits) == 1
    assert habits[0]['title'] == 'Meditar'


@pytest.mark.asyncio
async def test_get_habit_by_id(session, client):
    habit = HabitFactory.create(title='Caminhada')
    session.add(habit)
    await session.commit()

    response = client.get(f'/habits/{habit.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'Caminhada'


def test_get_habit_not_found(client):
    response = client.get('/habits/999')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Habit not found.'}


@pytest.mark.asyncio
async def test_patch_habit(session, client):
    habit = HabitFactory.create(title='Alongamento', is_active=True)
    session.add(habit)
    await session.commit()

    response = client.patch(
        f'/habits/{habit.id}',
        json={'is_active': False, 'title': 'Alongamento Matinal'},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['is_active'] is False
    assert response.json()['title'] == 'Alongamento Matinal'


def test_patch_habit_not_found(client):
    response = client.patch('/habits/999', json={'title': 'Novo'})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Habit not found.'}


@pytest.mark.asyncio
async def test_delete_habit(session, client):
    habit = HabitFactory.create(title='Dormir cedo')
    session.add(habit)
    await session.commit()

    response = client.delete(f'/habits/{habit.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'Habit has been deleted successfully.'
    }

    get_response = client.get(f'/habits/{habit.id}')
    assert get_response.status_code == HTTPStatus.NOT_FOUND


def test_delete_habit_not_found(client):
    response = client.delete('/habits/999')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Habit not found.'}


def test_habits_without_bot_api_key(session):
    def get_session_override():
        return session

    with TestClient(app) as unauth_client:
        app.dependency_overrides[get_session] = get_session_override
        response = unauth_client.get('/habits/')
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_daily_habits(session, client):
    habit1 = HabitFactory.create(
        title='Beber água',
        user_id=12345,
        recurrence=RecurrencePeriod.daily,
    )
    habit2 = HabitFactory.create(
        title='Caminhar',
        user_id=12345,
        recurrence=RecurrencePeriod.daily,
    )
    session.add_all([habit1, habit2])
    await session.commit()

    response = client.get('/habits/daily?telegram_id=12345')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'date' in data
    assert len(data['habits']) == 2
    assert data['habits'][0]['status'] == 'pending'
    assert data['habits'][1]['status'] == 'pending'


@pytest.mark.asyncio
async def test_get_daily_habits_with_checkin(session, client):
    habit = HabitFactory.create(
        title='Orar',
        user_id=555,
        recurrence=RecurrencePeriod.daily,
    )
    session.add(habit)
    await session.commit()

    today_str = date.today().isoformat()

    # Perform check-in
    checkin_response = client.post(
        f'/habits/{habit.id}/checkin',
        json={'date': today_str, 'status': 'done', 'notes': 'Feito pela manhã'},
    )
    assert checkin_response.status_code == HTTPStatus.CREATED
    assert checkin_response.json()['status'] == 'done'

    # Verify daily endpoint returns status 'done'
    daily_res = client.get(f'/habits/daily?telegram_id=555&date={today_str}')
    assert daily_res.status_code == HTTPStatus.OK
    habits = daily_res.json()['habits']
    assert len(habits) == 1
    assert habits[0]['status'] == 'done'


@pytest.mark.asyncio
async def test_get_daily_habits_filters_by_user_and_active(session, client):
    user_habit = HabitFactory.create(
        user_id=999,
        is_active=True,
        recurrence=RecurrencePeriod.daily,
    )
    other_user_habit = HabitFactory.create(
        user_id=888,
        is_active=True,
        recurrence=RecurrencePeriod.daily,
    )
    inactive_habit = HabitFactory.create(
        user_id=999,
        is_active=False,
        recurrence=RecurrencePeriod.daily,
    )
    session.add_all([user_habit, other_user_habit, inactive_habit])
    await session.commit()

    response = client.get('/habits/daily?telegram_id=999')
    assert response.status_code == HTTPStatus.OK
    habits = response.json()['habits']
    assert len(habits) == 1
    assert habits[0]['id'] == user_habit.id


@pytest.mark.asyncio
async def test_get_daily_habits_weekly_recurrence(session, client):
    # Today's weekday
    today = date.today()
    wday = today.weekday()
    other_wday = (wday + 1) % 7

    matching_habit = HabitFactory.create(
        user_id=111,
        recurrence=RecurrencePeriod.weekly,
        recurrence_days=[wday],
    )
    non_matching_habit = HabitFactory.create(
        user_id=111,
        recurrence=RecurrencePeriod.weekly,
        recurrence_days=[other_wday],
    )
    session.add_all([matching_habit, non_matching_habit])
    await session.commit()

    response = client.get(
        f'/habits/daily?telegram_id=111&date={today.isoformat()}'
    )
    assert response.status_code == HTTPStatus.OK
    habits = response.json()['habits']
    assert len(habits) == 1
    assert habits[0]['id'] == matching_habit.id


@pytest.mark.asyncio
async def test_checkin_updates_existing_log(session, client):
    habit = HabitFactory.create(user_id=321)
    session.add(habit)
    await session.commit()

    today_str = date.today().isoformat()

    # First checkin: done
    res1 = client.post(
        f'/habits/{habit.id}/checkin',
        json={'date': today_str, 'status': 'done'},
    )
    assert res1.status_code == HTTPStatus.CREATED
    assert res1.json()['status'] == 'done'

    # Second checkin on same day: update to skipped
    res2 = client.post(
        f'/habits/{habit.id}/checkin',
        json={'date': today_str, 'status': 'skipped'},
    )
    assert res2.status_code == HTTPStatus.CREATED
    assert res2.json()['status'] == 'skipped'

    # Check daily reflects skipped
    daily_res = client.get(f'/habits/daily?telegram_id=321&date={today_str}')
    assert daily_res.json()['habits'][0]['status'] == 'skipped'


@pytest.mark.asyncio
async def test_habit_stats_and_logs(session, client):
    habit = HabitFactory.create(
        user_id=777,
        recurrence=RecurrencePeriod.daily,
    )
    session.add(habit)
    await session.commit()

    today = date.today()
    client.post(
        f'/habits/{habit.id}/checkin',
        json={'date': today.isoformat(), 'status': 'done'},
    )

    stats_res = client.get(f'/habits/{habit.id}/stats')
    assert stats_res.status_code == HTTPStatus.OK
    stats = stats_res.json()
    assert stats['habit_id'] == habit.id
    assert stats['completed_days'] == 1
    assert stats['current_streak'] >= 1

    logs_res = client.get(f'/habits/{habit.id}/logs')
    assert logs_res.status_code == HTTPStatus.OK
    logs = logs_res.json()['logs']
    assert len(logs) == 1
    assert logs[0]['status'] == 'done'

