from datetime import date, datetime
from enum import Enum

from sqlalchemy import JSON, BigInteger, ForeignKey, UniqueConstraint, func

from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    registry,
    relationship,
)

table_registry = registry()


class TodoState(str, Enum):
    draft = 'draft'
    todo = 'todo'
    doing = 'doing'
    done = 'done'
    trash = 'trash'


class RecurrencePeriod(str, Enum):
    none = 'none'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'


@mapped_as_dataclass(table_registry, kw_only=True)
class User:
    __tablename__ = 'users'

    id: Mapped[int | None] = mapped_column(
        BigInteger, primary_key=True, default=None
    )
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    todos: Mapped[list['Todo']] = relationship(
        init=False,
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    habits: Mapped[list['Habit']] = relationship(
        init=False,
        cascade='all, delete-orphan',
        lazy='selectin',
    )


@mapped_as_dataclass(table_registry)
class Todo:
    __tablename__ = 'todos'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    state: Mapped[TodoState]
    recurrence: Mapped[RecurrencePeriod] = mapped_column(
        default=RecurrencePeriod.none
    )
    recurrence_days: Mapped[list[int] | None] = mapped_column(
        JSON, default=None, nullable=True
    )
    due_date: Mapped[datetime | None] = mapped_column(
        default=None, nullable=True
    )

    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey('users.id'), nullable=True, default=None
    )

    # user: Mapped[User] = relationship(init=False, back_populates='todos')

    # Exercício 01
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )


@mapped_as_dataclass(table_registry)
class Habit:
    __tablename__ = 'habits'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    title: Mapped[str]
    description: Mapped[str] = mapped_column(default='')
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey('users.id'), nullable=True, default=None
    )
    recurrence: Mapped[RecurrencePeriod] = mapped_column(
        default=RecurrencePeriod.daily
    )
    recurrence_days: Mapped[list[int] | None] = mapped_column(
        JSON, default=None, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    logs: Mapped[list['HabitLog']] = relationship(
        init=False,
        cascade='all, delete-orphan',
        lazy='selectin',
    )


@mapped_as_dataclass(table_registry)
class HabitLog:
    __tablename__ = 'habit_logs'
    __table_args__ = (
        UniqueConstraint('habit_id', 'date', name='uq_habit_log_habit_date'),
    )

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey('habits.id', ondelete='CASCADE')
    )
    date: Mapped[date]
    status: Mapped[str] = mapped_column(default='done')
    notes: Mapped[str | None] = mapped_column(default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )


