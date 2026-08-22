import calendar
from datetime import datetime, timedelta
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


def calculate_next_due_date(
    base_date: datetime | None, period: RecurrencePeriod
) -> datetime:
    base = base_date or datetime.now()
    if period == RecurrencePeriod.daily:
        return base + timedelta(days=1)
    elif period == RecurrencePeriod.weekly:
        return base + timedelta(weeks=1)
    elif period == RecurrencePeriod.monthly:
        month = base.month - 1 + 1
        year = base.year + month // 12
        month = month % 12 + 1
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
        due_date=todo.due_date,
    )

    session.add(db_todo)
    await session.commit()
    await session.refresh(db_todo)

    return db_todo


@router.get('/', response_model=TodoList)
async def list_todos(
    session: Session,
    todo_filter: FilterTodo = Depends(),
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
            db_todo.due_date, db_todo.recurrence
        )
        next_todo = Todo(
            title=db_todo.title,
            description=db_todo.description,
            state=TodoState.todo,
            user_id=db_todo.user_id,
            recurrence=db_todo.recurrence,
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

