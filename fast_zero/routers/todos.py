import calendar
from datetime import date, datetime, timedelta
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_zero.database import get_session
from fast_zero.models import RecurrencePeriod, Todo, TodoState
from fast_zero.schemas import (
    FilterTodo,
    Message,
    TodoList,
    TodoPublic,
    TodoScheduleItem,
    TodoScheduleResponse,
    TodoSchema,
    TodoUpdate,
)
from fast_zero.security import verify_bot_token

Session = Annotated[AsyncSession, Depends(get_session)]
router = APIRouter(
    prefix='/todos',
    tags=['todos'],
    dependencies=[Depends(verify_bot_token)],
)


def _next_month(year: int, month: int) -> tuple[int, int]:
    m = month % 12 + 1
    y = year + (month // 12)
    return y, m


def calculate_next_due_date(
    base_date: datetime | None,
    period: RecurrencePeriod,
    recurrence_days: list[int] | None = None,
) -> datetime:
    base = base_date or datetime.now()
    if period == RecurrencePeriod.daily:
        return base + timedelta(days=1)
    elif period == RecurrencePeriod.weekly:
        if recurrence_days:
            valid_days = sorted(set(recurrence_days))
            w = base.weekday()
            min_delta = min(
                (d - w) if d > w else (7 - w + d) for d in valid_days
            )
            return base + timedelta(days=min_delta)
        return base + timedelta(weeks=1)
    elif period == RecurrencePeriod.monthly:
        if recurrence_days:
            valid_days = sorted(set(recurrence_days))
            future_days_this_month = [d for d in valid_days if d > base.day]
            if future_days_this_month:
                target_day = future_days_this_month[0]
                year, month = base.year, base.month
            else:
                year, month = _next_month(base.year, base.month)
                target_day = valid_days[0]
            max_day = calendar.monthrange(year, month)[1]
            return base.replace(
                year=year, month=month, day=min(target_day, max_day)
            )
        year, month = _next_month(base.year, base.month)
        day = min(base.day, calendar.monthrange(year, month)[1])
        return base.replace(year=year, month=month, day=day)
    return base


@router.post('/', response_model=TodoPublic)
async def create_todo(
    todo: TodoSchema,
    session: Session,
):
    print(todo)
    db_todo = Todo(
        title=todo.title,
        description=todo.description,
        state=todo.state,
        user_id=todo.user_id,
        recurrence=todo.recurrence,
        recurrence_days=todo.recurrence_days,
        due_date=todo.due_date,
    )

    session.add(db_todo)
    await session.commit()
    await session.refresh(db_todo)

    return db_todo


def _matches_recurrence(
    todo: Todo, target_date: date, base_date: date
) -> bool:
    if todo.recurrence == RecurrencePeriod.daily:
        return True
    if todo.recurrence == RecurrencePeriod.weekly:
        if todo.recurrence_days:
            return target_date.weekday() in todo.recurrence_days
        return target_date.weekday() == base_date.weekday()
    if todo.recurrence == RecurrencePeriod.monthly:
        last_day = calendar.monthrange(target_date.year, target_date.month)[1]
        if todo.recurrence_days:
            return any(
                target_date.day == min(d, last_day)
                for d in todo.recurrence_days
            )
        return target_date.day == min(base_date.day, last_day)
    return False


def project_todo_on_date(
    todo: Todo, target_date: date
) -> TodoScheduleItem | None:
    if todo.state == TodoState.trash:
        return None

    base_datetime = todo.due_date or todo.created_at
    base_date = base_datetime.date() if base_datetime else target_date
    todo_time = (
        base_datetime.time() if base_datetime else datetime.min.time()
    )

    if todo.due_date and todo.due_date.date() == target_date:
        return TodoScheduleItem(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            state=todo.state,
            user_id=todo.user_id,
            recurrence=todo.recurrence,
            recurrence_days=todo.recurrence_days,
            due_date=todo.due_date,
            is_recurring_occurrence=False,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )

    if todo.recurrence == RecurrencePeriod.none or target_date < base_date:
        return None

    if _matches_recurrence(todo, target_date, base_date):
        projected_due_date = datetime.combine(target_date, todo_time)
        return TodoScheduleItem(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            state=TodoState.todo,
            user_id=todo.user_id,
            recurrence=todo.recurrence,
            recurrence_days=todo.recurrence_days,
            due_date=projected_due_date,
            is_recurring_occurrence=True,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )

    return None


@router.get('/schedule', response_model=TodoScheduleResponse)
async def get_schedule(
    session: Session,
    date: date | None = None,
    telegram_id: int | None = None,
):
    target_date = date or datetime.now().date()
    query = select(Todo).where(Todo.state != TodoState.trash)

    if telegram_id:
        query = query.filter(Todo.user_id == telegram_id)

    db_todos = await session.scalars(query)
    scheduled_todos: list[TodoScheduleItem] = []

    for todo in db_todos.all():
        item = project_todo_on_date(todo, target_date)
        if item:
            scheduled_todos.append(item)

    return TodoScheduleResponse(date=target_date, todos=scheduled_todos)


@router.get('/', response_model=TodoList)
async def list_todos(
    session: Session,
    todo_filter: Annotated[FilterTodo, Query()],
):
    query = select(Todo)

    if todo_filter.telegram_id:
        query = query.filter(Todo.user_id == todo_filter.telegram_id)

    if todo_filter.title:
        query = query.filter(Todo.title.contains(todo_filter.title))

    if todo_filter.description:
        query = query.filter(
            Todo.description.contains(todo_filter.description)
        )

    if todo_filter.state:
        query = query.filter(Todo.state == todo_filter.state)

    if todo_filter.recurrence:
        query = query.filter(Todo.recurrence == todo_filter.recurrence)

    todos = await session.scalars(
        query.offset(todo_filter.offset).limit(todo_filter.limit)
    )

    return {'todos': todos.all()}


@router.patch('/{todo_id}', response_model=TodoPublic)
async def patch_todo(todo_id: int, session: Session, todo: TodoUpdate):
    db_todo = await session.scalar(select(Todo).where(Todo.id == todo_id))

    if not db_todo:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Task not found.'
        )

    previous_state = db_todo.state

    for key, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, key, value)

    session.add(db_todo)

    if (
        previous_state != TodoState.done
        and db_todo.state == TodoState.done
        and db_todo.recurrence != RecurrencePeriod.none
    ):
        next_due = calculate_next_due_date(
            db_todo.due_date, db_todo.recurrence, db_todo.recurrence_days
        )
        next_todo = Todo(
            title=db_todo.title,
            description=db_todo.description,
            state=TodoState.todo,
            user_id=db_todo.user_id,
            recurrence=db_todo.recurrence,
            recurrence_days=db_todo.recurrence_days,
            due_date=next_due,
        )
        session.add(next_todo)

    await session.commit()
    await session.refresh(db_todo)

    return db_todo


@router.delete('/{todo_id}', response_model=Message)
async def delete_todo(todo_id: int, session: Session):
    todo = await session.scalar(select(Todo).where(Todo.id == todo_id))

    if not todo:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Task not found.'
        )

    await session.delete(todo)
    await session.commit()

    return {'message': 'Task has been deleted successfully.'}
