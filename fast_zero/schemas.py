from datetime import date as dt_date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from fast_zero.models import RecurrencePeriod, TodoState


class Message(BaseModel):
    message: str


class UserSchema(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list[UserPublic]


class Token(BaseModel):
    access_token: str
    token_type: str


class FilterPage(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


MIN_WEEKDAY = 0
MAX_WEEKDAY = 6
MIN_MONTH_DAY = 1
MAX_MONTH_DAY = 31


class TodoSchema(BaseModel):
    title: str
    description: str
    state: TodoState
    user_id: int | None = None
    recurrence: RecurrencePeriod = RecurrencePeriod.none
    recurrence_days: list[int] | None = None
    due_date: datetime | None = None

    @model_validator(mode='after')
    def validate_recurrence_days(self) -> 'TodoSchema':
        if self.recurrence_days:
            if self.recurrence == RecurrencePeriod.weekly:
                for day in self.recurrence_days:
                    if day < MIN_WEEKDAY or day > MAX_WEEKDAY:
                        raise ValueError(
                            'Weekly recurrence days must be integers '
                            'between 0 (Monday) and 6 (Sunday).'
                        )
            elif self.recurrence == RecurrencePeriod.monthly:
                for day in self.recurrence_days:
                    if day < MIN_MONTH_DAY or day > MAX_MONTH_DAY:
                        raise ValueError(
                            'Monthly recurrence days must be integers '
                            'between 1 and 31.'
                        )
        return self


class TodoPublic(TodoSchema):
    id: int
    created_at: datetime
    updated_at: datetime


class TodoList(BaseModel):
    todos: list[TodoPublic]


class TodoScheduleItem(BaseModel):
    id: int
    title: str
    description: str
    state: TodoState
    user_id: int | None = None
    recurrence: RecurrencePeriod = RecurrencePeriod.none
    recurrence_days: list[int] | None = None
    due_date: datetime | None = None
    is_recurring_occurrence: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TodoScheduleResponse(BaseModel):
    date: dt_date
    todos: list[TodoScheduleItem]


class FilterTodo(FilterPage):
    telegram_id: int | None = None
    title: str | None = Field(None, min_length=3, max_length=20)
    description: str | None = Field(None, min_length=3, max_length=20)
    state: TodoState | None = None
    recurrence: RecurrencePeriod | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    state: TodoState | None = None
    recurrence: RecurrencePeriod | None = None
    recurrence_days: list[int] | None = None
    due_date: datetime | None = None

    @model_validator(mode='after')
    def validate_recurrence_days(self) -> 'TodoUpdate':
        if self.recurrence_days:
            if self.recurrence == RecurrencePeriod.weekly:
                for day in self.recurrence_days:
                    if day < MIN_WEEKDAY or day > MAX_WEEKDAY:
                        raise ValueError(
                            'Weekly recurrence days must be integers '
                            'between 0 (Monday) and 6 (Sunday).'
                        )
            elif self.recurrence == RecurrencePeriod.monthly:
                for day in self.recurrence_days:
                    if day < MIN_MONTH_DAY or day > MAX_MONTH_DAY:
                        raise ValueError(
                            'Monthly recurrence days must be integers '
                            'between 1 and 31.'
                        )
            elif self.recurrence is None:
                for day in self.recurrence_days:
                    if day < MIN_WEEKDAY or day > MAX_MONTH_DAY:
                        raise ValueError(
                            'Recurrence days must be valid weekday (0-6) '
                            'or month day (1-31).'
                        )
        return self


class HabitSchema(BaseModel):
    title: str
    description: str = ''
    user_id: int | None = None
    recurrence: RecurrencePeriod = RecurrencePeriod.daily
    recurrence_days: list[int] | None = None
    is_active: bool = True

    @model_validator(mode='after')
    def validate_recurrence_days(self) -> 'HabitSchema':
        if self.recurrence_days:
            if self.recurrence == RecurrencePeriod.weekly:
                for day in self.recurrence_days:
                    if day < MIN_WEEKDAY or day > MAX_WEEKDAY:
                        raise ValueError(
                            'Weekly recurrence days must be integers '
                            'between 0 (Monday) and 6 (Sunday).'
                        )
            elif self.recurrence == RecurrencePeriod.monthly:
                for day in self.recurrence_days:
                    if day < MIN_MONTH_DAY or day > MAX_MONTH_DAY:
                        raise ValueError(
                            'Monthly recurrence days must be integers '
                            'between 1 and 31.'
                        )
        return self


class HabitPublic(HabitSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class HabitList(BaseModel):
    habits: list[HabitPublic]


class FilterHabit(FilterPage):
    telegram_id: int | None = None
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    recurrence: RecurrencePeriod | None = None


class HabitUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    recurrence: RecurrencePeriod | None = None
    recurrence_days: list[int] | None = None
    is_active: bool | None = None

    @model_validator(mode='after')
    def validate_recurrence_days(self) -> 'HabitUpdate':
        if self.recurrence_days:
            if self.recurrence == RecurrencePeriod.weekly:
                for day in self.recurrence_days:
                    if day < MIN_WEEKDAY or day > MAX_WEEKDAY:
                        raise ValueError(
                            'Weekly recurrence days must be integers '
                            'between 0 (Monday) and 6 (Sunday).'
                        )
            elif self.recurrence == RecurrencePeriod.monthly:
                for day in self.recurrence_days:
                    if day < MIN_MONTH_DAY or day > MAX_MONTH_DAY:
                        raise ValueError(
                            'Monthly recurrence days must be integers '
                            'between 1 and 31.'
                        )
            elif self.recurrence is None:
                for day in self.recurrence_days:
                    if day < MIN_WEEKDAY or day > MAX_MONTH_DAY:
                        raise ValueError(
                            'Recurrence days must be valid weekday (0-6) '
                            'or month day (1-31).'
                        )
        return self


class HabitDailyItem(BaseModel):
    id: int
    title: str
    description: str
    user_id: int | None = None
    recurrence: RecurrencePeriod = RecurrencePeriod.daily
    recurrence_days: list[int] | None = None
    is_active: bool = True
    status: str = 'pending'
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class HabitDailyResponse(BaseModel):
    date: dt_date
    habits: list[HabitDailyItem]


class HabitCheckinSchema(BaseModel):
    date: dt_date | None = None
    status: str = 'done'
    notes: str | None = None


class HabitLogPublic(BaseModel):
    id: int
    habit_id: int
    date: dt_date
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class HabitLogList(BaseModel):
    logs: list[HabitLogPublic]


class HabitStatsResponse(BaseModel):
    habit_id: int
    current_streak: int = 0
    longest_streak: int = 0
    completion_rate: float = 0.0
    total_scheduled_days: int = 0
    completed_days: int = 0
    missed_days: int = 0
    skipped_days: int = 0


