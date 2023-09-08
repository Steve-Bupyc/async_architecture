import sys

from fastapi.security import OAuth2PasswordBearer

# DB settings
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_SCHEMA = "task_manager"

# Services
RABBITMQ_SERVICE_URL = "amqp://guest:guest@localhost:5672/"
USERS_STREAM_EXCHANGE = "users-stream"
TASKS_STREAM_EXCHANGE = "tasks-stream"
USERS_LIFECYCLE_EXCHANGE = "users-lifecycle"
TASKS_LIFECYCLE_EXCHANGE = "tasks-lifecycle"
USER_CREATED = "Users.Created"
USER_UPDATED = "Users.Updated"
USER_ROLE_CHANGED = "Users.RoleChanged"
TASK_CREATED = "Tasks.Created"
TASK_UPDATED = "Tasks.Updated"
TASK_ADDED = "Tasks.Added"
TASK_ASSIGNED = "Tasks.Assigned"
TASK_COMPLETED = "Tasks.Completed"
AUTH_SERVICE_URL = "http://localhost:8080"
TASK_MANAGER_URL = "http://localhost:8081"

# APP settings
SECRET_KEY = "e8e2d862e49058382259f2e34a9d3854331c05c25b198b8cdc6a728ab24b3114"
# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"

# add SchemaRegistryValidator to the system path
sys.path.insert(0, "/mnt/d/work/Projects/async architecture/async_architecture/")

ORIGINS = [AUTH_SERVICE_URL, TASK_MANAGER_URL]

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{AUTH_SERVICE_URL}/token", scopes={"task-manager": "Access to Task Manager Service"}
)
