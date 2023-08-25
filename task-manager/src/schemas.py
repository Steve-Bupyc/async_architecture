import re
from uuid import UUID

from pydantic import BaseModel, field_validator
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
    @field_validator("title")
    def title_must_be_without_brackets(cls, v: str) -> str:
        result = re.match("/[^\]\[]/", v)
        if result:
            raise ValueError("Title must be without brackets")

        return v


class TaskResponseSchema(TaskBaseSchema):
    guid: UUID
    is_done: bool

    class Config:
        from_attributes = True
