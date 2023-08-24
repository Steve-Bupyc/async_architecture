import re
from uuid import UUID

from pydantic import BaseModel
from src.db.base import Roles


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


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
    title: str = ...
    jira_id: str = ...
    description: str = ...


class TaskCreateSchema(TaskBaseSchema):
    pass
