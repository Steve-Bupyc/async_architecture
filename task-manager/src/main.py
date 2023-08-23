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


@app.post("/tasks/create/", response_model=TaskResponseSchema)
async def create_task(
    task: TaskCreateSchema, current_user: Annotated[User, Security(get_current_active_user, scopes=["task-manager"])]
):
    return await Task.create(task, current_user.guid)


@app.post("/tasks/shuffle/", response_model=list[TaskResponseSchema])
async def shuffle_task(current_user: Annotated[User, Security(get_current_active_user, scopes=["task-manager"])]):
    if current_user.role not in {Roles.admin, Roles.manager}:
        raise PermissionDenied

    return await Task.shuffle_tasks()


@app.post("/tasks/{guid}/complete/", response_model=TaskResponseSchema)
async def complete_task(
    guid: UUID, current_user: Annotated[User, Security(get_current_active_user, scopes=["task-manager"])]
):
    db_task = await Task.get(guid)
    if db_task.is_done:
        return db_task

    if current_user.role not in {Roles.admin, Roles.manager} and db_task.assigned_to != current_user.guid:
        raise PermissionDenied

    return await Task.complete(guid)


@app.get("/tasks/my/", response_model=list[TaskResponseSchema])
async def get_my_tasks(current_user: Annotated[User, Security(get_current_active_user, scopes=["task-manager"])]):
    return current_user.assigned_tasks
