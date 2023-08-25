from uuid import UUID

from pydantic import BaseModel
from src.db.base import Roles, Types


class TokenData(BaseModel):
    username: str = None
    scopes: list[str] = []


class UserBaseSchema(BaseModel):
    username: str = ...
    full_name: str | None = None
    role: Roles = Roles.worker


class UserCreateSchema(UserBaseSchema):
    guid: UUID


class UserUpdateSchema(BaseModel):
    is_active: bool


class TaskBaseSchema(BaseModel):
    guid: UUID
    title: str = ...
    jira_id: str = ...
    description: str = ...
    assigned_to: UUID


class TaskCreateSchema(TaskBaseSchema):
    pass


class TaskUpdateSchema(TaskBaseSchema):
    is_done: bool


class TransactionBaseSchema(BaseModel):
    amount: int
    type: Types
    description: str


class TransactionCreateSchema(TransactionBaseSchema):
    user_guid: UUID


class StatisticsTotalResponseSchema(BaseModel):
    total_earned: int


class MyStatisticsResponseSchema(BaseModel):
    balance: int
    transactions: list[TransactionBaseSchema]
