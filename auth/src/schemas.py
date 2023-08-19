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
    password: str = ...


class UserUpdateSchema(UserBaseSchema):
    username: str = None
    password: str = None
    full_name: str = None
    role: Roles = None
    is_active: bool = None


class UserResponseSchema(UserBaseSchema):
    guid: UUID
    is_active: bool | None = None

    class Config:
        from_attributes = True
