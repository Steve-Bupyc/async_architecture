from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends
from fastapi.security import SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError
from src.config import *
from src.db.models import User
from src.exceptions import InactiveUser, InvalidCredentials, PermissionDenied
from src.schemas import TokenData


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + ACCESS_TOKEN_EXPIRE_MINUTES

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


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

    user = await User.get_by_email(token_data.username)
    if user is None:
        raise InvalidCredentials()

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise PermissionDenied()

    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise InactiveUser()

    return current_user
