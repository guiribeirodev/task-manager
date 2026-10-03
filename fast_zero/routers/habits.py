import calendar
from datetime import date, datetime, timedelta
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_zero.database import get_session
from fast_zero.models import Habit, HabitLog, RecurrencePeriod
from fast_zero.schemas import (
    FilterHabit,
    HabitCheckinSchema,
    HabitDailyItem,
    HabitDailyResponse,
    HabitList,
    HabitLogList,
    HabitLogPublic,
    HabitPublic,
    HabitSchema,
    HabitStatsResponse,
    HabitUpdate,
    Message,
)
from fast_zero.security import verify_bot_token

Session = Annotated[AsyncSession, Depends(get_session)]
router = APIRouter(
    prefix='/habits',
    tags=['habits'],
    dependencies=[Depends(verify_bot_token)],
)


def _matches_habit_recurrence(habit: Habit, target_date: date) -> bool:
    if habit.recurrence == RecurrencePeriod.daily:
        return True
    if habit.recurrence == RecurrencePeriod.weekly:
        if habit.recurrence_days:
            return target_date.weekday() in habit.recurrence_days
        return True
    if habit.recurrence == RecurrencePeriod.monthly:
        last_day = calendar.monthrange(target_date.year, target_date.month)[1]
        if habit.recurrence_days:
            return any(
                target_date.day == min(d, last_day)
                for d in habit.recurrence_days
            )
        base_day = habit.created_at.day if habit.created_at else 1
        return target_date.day == min(base_day, last_day)
    if habit.recurrence == RecurrencePeriod.none:
        created_date = (
            habit.created_at.date() if habit.created_at else target_date
        )
        return target_date == created_date
    return True


@router.post('/', response_model=HabitPublic, status_code=HTTPStatus.CREATED)
async def create_habit(
    habit: HabitSchema,
    session: Session,
):
    db_habit = Habit(
        title=habit.title,
        description=habit.description,
        user_id=habit.user_id,
        recurrence=habit.recurrence,
        recurrence_days=habit.recurrence_days,
        is_active=habit.is_active,
    )

    session.add(db_habit)
    await session.commit()
    await session.refresh(db_habit)

    return db_habit


@router.get('/daily', response_model=HabitDailyResponse)
async def get_daily_habits(
    session: Session,
    telegram_id: int | None = None,
    date: date | None = None,
):
    target_date = date or datetime.now().date()
    query = select(Habit).where(Habit.is_active.is_(True))

    if telegram_id:
        query = query.filter(Habit.user_id == telegram_id)

    db_habits = (await session.scalars(query)).all()

    matching_habits: list[Habit] = []
    for habit in db_habits:
        created_date = (
            habit.created_at.date() if habit.created_at else target_date
        )
        if target_date < created_date:
            continue
        if _matches_habit_recurrence(habit, target_date):
            matching_habits.append(habit)

    status_map: dict[int, str] = {}
    if matching_habits:
        habit_ids = [h.id for h in matching_habits]
        logs_query = select(HabitLog).where(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.date == target_date,
        )
        logs = (await session.scalars(logs_query)).all()
        status_map = {log.habit_id: log.status for log in logs}

    daily_items = [
        HabitDailyItem(
            id=habit.id,
            title=habit.title,
            description=habit.description,
            user_id=habit.user_id,
            recurrence=habit.recurrence,
            recurrence_days=habit.recurrence_days,
            is_active=habit.is_active,
            status=status_map.get(habit.id, 'pending'),
            created_at=habit.created_at,
            updated_at=habit.updated_at,
        )
        for habit in matching_habits
    ]

    return HabitDailyResponse(date=target_date, habits=daily_items)


@router.get('/', response_model=HabitList)
async def list_habits(
    session: Session,
    habit_filter: Annotated[FilterHabit, Query()],
):
    query = select(Habit)

    if habit_filter.telegram_id:
        query = query.filter(Habit.user_id == habit_filter.telegram_id)

    if habit_filter.title:
        query = query.filter(Habit.title.contains(habit_filter.title))

    if habit_filter.description:
        query = query.filter(
            Habit.description.contains(habit_filter.description)
        )

    if habit_filter.is_active is not None:
        query = query.filter(Habit.is_active == habit_filter.is_active)

    if habit_filter.recurrence:
        query = query.filter(Habit.recurrence == habit_filter.recurrence)

    habits = await session.scalars(
        query.offset(habit_filter.offset).limit(habit_filter.limit)
    )

    return {'habits': habits.all()}


@router.get('/{habit_id}', response_model=HabitPublic)
async def get_habit(habit_id: int, session: Session):
    db_habit = await session.scalar(select(Habit).where(Habit.id == habit_id))

    if not db_habit:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Habit not found.'
        )

    return db_habit


@router.patch('/{habit_id}', response_model=HabitPublic)
async def patch_habit(habit_id: int, session: Session, habit: HabitUpdate):
    db_habit = await session.scalar(select(Habit).where(Habit.id == habit_id))

    if not db_habit:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Habit not found.'
        )

    for key, value in habit.model_dump(exclude_unset=True).items():
        setattr(db_habit, key, value)

    session.add(db_habit)
    await session.commit()
    await session.refresh(db_habit)

    return db_habit


@router.delete('/{habit_id}', response_model=Message)
async def delete_habit(habit_id: int, session: Session):
    habit = await session.scalar(select(Habit).where(Habit.id == habit_id))

    if not habit:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Habit not found.'
        )

    await session.delete(habit)
    await session.commit()

    return {'message': 'Habit has been deleted successfully.'}


@router.post(
    '/{habit_id}/checkin',
    response_model=HabitLogPublic,
    status_code=HTTPStatus.CREATED,
)
async def checkin_habit(
    habit_id: int,
    checkin_data: HabitCheckinSchema,
    session: Session,
):
    habit = await session.scalar(select(Habit).where(Habit.id == habit_id))
    if not habit:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Habit not found.'
        )

    checkin_date = checkin_data.date or datetime.now().date()

    existing_log = await session.scalar(
        select(HabitLog).where(
            HabitLog.habit_id == habit_id, HabitLog.date == checkin_date
        )
    )

    if existing_log:
        existing_log.status = checkin_data.status
        if checkin_data.notes is not None:
            existing_log.notes = checkin_data.notes
        db_log = existing_log
    else:
        db_log = HabitLog(
            habit_id=habit_id,
            date=checkin_date,
            status=checkin_data.status,
            notes=checkin_data.notes,
        )
        session.add(db_log)

    await session.commit()
    await session.refresh(db_log)

    return db_log


@router.get('/{habit_id}/stats', response_model=HabitStatsResponse)
async def get_habit_stats(habit_id: int, session: Session):
    habit = await session.scalar(select(Habit).where(Habit.id == habit_id))
    if not habit:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Habit not found.'
        )

    logs = (
        await session.scalars(
            select(HabitLog)
            .where(HabitLog.habit_id == habit_id)
            .order_by(HabitLog.date.asc())
        )
    ).all()

    today = datetime.now().date()
    created_date = habit.created_at.date() if habit.created_at else today

    scheduled_dates: list[date] = []
    cur = created_date
    while cur <= today:
        if _matches_habit_recurrence(habit, cur):
            scheduled_dates.append(cur)
        cur += timedelta(days=1)

    total_scheduled_days = len(scheduled_dates)
    log_by_date = {log.date: log.status for log in logs}

    completed_days = sum(1 for s in log_by_date.values() if s == 'done')
    missed_days = sum(1 for s in log_by_date.values() if s == 'missed')
    skipped_days = sum(1 for s in log_by_date.values() if s == 'skipped')

    completion_rate = (
        (completed_days / total_scheduled_days * 100.0)
        if total_scheduled_days > 0
        else 0.0
    )

    longest_streak = 0
    running_streak = 0

    for d in scheduled_dates:
        st = log_by_date.get(d)
        if st == 'done':
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        elif st == 'skipped':
            continue
        else:
            running_streak = 0

    back_streak = 0
    for d in reversed(scheduled_dates):
        st = log_by_date.get(d)
        if d == today and st is None:
            continue
        if st == 'done':
            back_streak += 1
        elif st == 'skipped':
            continue
        else:
            break
    current_streak = back_streak

    return HabitStatsResponse(
        habit_id=habit_id,
        current_streak=current_streak,
        longest_streak=longest_streak,
        completion_rate=round(completion_rate, 1),
        total_scheduled_days=total_scheduled_days,
        completed_days=completed_days,
        missed_days=missed_days,
        skipped_days=skipped_days,
    )


@router.get('/{habit_id}/logs', response_model=HabitLogList)
async def get_habit_logs(
    habit_id: int,
    session: Session,
    from_date: date | None = None,
    to_date: date | None = None,
    status: str | None = None,
):
    habit = await session.scalar(select(Habit).where(Habit.id == habit_id))
    if not habit:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Habit not found.'
        )

    query = select(HabitLog).where(HabitLog.habit_id == habit_id)
    if from_date:
        query = query.filter(HabitLog.date >= from_date)
    if to_date:
        query = query.filter(HabitLog.date <= to_date)
    if status:
        query = query.filter(HabitLog.status == status)

    query = query.order_by(HabitLog.date.desc())
    logs = (await session.scalars(query)).all()
    return {'logs': logs}
