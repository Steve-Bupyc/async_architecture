from typing import Annotated

from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from src.db.base import Base, engine
from src.db.models import Task, User
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


@app.get("/tasks/my/", response_model=list[TaskResponseSchema])
async def get_my_tasks(current_user: Annotated[User, Security(get_current_active_user, scopes=["task-manager"])]):
    return current_user.assigned_tasks
