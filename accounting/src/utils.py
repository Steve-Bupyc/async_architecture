from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError
from src.config import *
from src.db.base import Roles
from src.db.models import User
from src.exceptions import InactiveUser, InvalidCredentials, PermissionDenied
from src.schemas import TokenData


async def get_current_user(security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise InvalidCredentials()

        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise InvalidCredentials()

    user = await User.get_by_username(token_data.username)
    if user is None:
        raise InvalidCredentials()

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise PermissionDenied()

    return user


async def get_current_active_user(current_user: Annotated[User, Security(get_current_user, scopes=["accounting"])]):
    if not current_user.is_active:
        raise InactiveUser()

    return current_user


async def get_allowed_user(current_user: Annotated[User, Security(get_current_user, scopes=["accounting"])]):
    if current_user.role not in {Roles.admin, Roles.accountant}:
        raise PermissionDenied

    return current_user
