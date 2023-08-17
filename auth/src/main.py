from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Security
from fastapi.security import OAuth2PasswordRequestForm

from src.config import *
from src.db.base import Base, Roles, engine
from src.db.models import User
from src.exceptions import AuthenticateFailed, PermissionDenied
from src.schemas import TokenSchema, UserCreateSchema, UserResponseSchema, UserUpdateSchema
from src.utils import create_access_token, get_current_active_user, get_current_user

app = FastAPI()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.post("/token", response_model=TokenSchema)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await User.authenticate(form_data.username, form_data.password)
    if not user:
        raise AuthenticateFailed

    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes}, expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/create/", response_model=UserResponseSchema)
async def create_user(user: UserCreateSchema):
    return await User.create(user)


@app.post("/users/{guid}/update/", response_model=UserResponseSchema)
async def create_user(
    guid: UUID, user: UserUpdateSchema, current_user: Annotated[User, Depends(get_current_active_user)]
):
    if current_user.role != Roles.admin and current_user.guid != guid:
        raise PermissionDenied

    return await User.update(guid, user)


@app.get("/users/me/", response_model=UserResponseSchema)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@app.get("/status/")
async def read_system_status(current_user: Annotated[User, Depends(get_current_user)]):
    return {"status": "ok"}
