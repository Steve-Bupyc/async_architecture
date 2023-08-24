from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from src.db.base import Base, Roles, engine
from src.db.models import Task, User
from src.exceptions import PermissionDenied
from src.schemas import TaskCreateSchema, TaskResponseSchema
from src.utils import get_current_active_user

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
