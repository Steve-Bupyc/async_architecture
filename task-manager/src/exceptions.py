from fastapi import HTTPException, status


class AuthenticateFailed(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "Incorrect username or password")


class InvalidCredentials(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")


class PermissionDenied(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Not enough permissions")


class InactiveUser(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail="Inactive user")
