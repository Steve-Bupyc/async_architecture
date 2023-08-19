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


class UserResponseSchema(UserBaseSchema):
    is_active: bool | None = None

    class Config:
        from_attributes = True


class UserCreatedRabbitSchema(UserBaseSchema):
    guid: UUID
    is_active: bool = False


class UserCreatedRabbitSchemaV1(BaseModel):
    id: UUID
    version: int
    name: str
    time: str
    producer: str
    data: UserCreatedRabbitSchema


class UserUpdatedRabbitSchema(UserBaseSchema):
    guid: UUID
    is_active: bool = False


class UserRoleChangedRabbitSchema(BaseModel):
    guid: UUID
    role: Roles = Roles.worker
    is_active: bool = False


class TaskBaseSchema(BaseModel):
    title: str = ...
    description: str = ...


class TaskCreateSchema(TaskBaseSchema):
    pass


class TaskResponseSchema(TaskBaseSchema):
    is_done: bool

    class Config:
        from_attributes = True
