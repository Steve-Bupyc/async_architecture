from uuid import UUID
from pydantic import BaseModel, validator

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
    is_active: bool | None = None

    class Config:
        from_attributes = True

class UserRabbitSchema(UserBaseSchema):
    guid: UUID
    
    @validator("guid")
    def convert_guid_to_str(cls, guid):
        return str(guid)

class UserCreatedRabbitSchema(UserRabbitSchema):
    is_active: bool = False

class UserUpdatedRabbitSchema(UserRabbitSchema):
    is_active: bool = False

class UserRoleChangedRabbitSchema(UserRabbitSchema):
    role: Roles = Roles.worker
    is_active: bool = False