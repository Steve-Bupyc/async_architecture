import sys
from datetime import timedelta

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

# DB settings
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_SCHEMA = "auth"

# Services
RABBITMQ_SERVICE_URL = "amqp://guest:guest@localhost:5672/"
USERS_STREAM_EXCHANGE = "users-stream"
USERS_LIFECYCLE_EXCHANGE = "users-lifecycle"
USER_CREATED = "Users.Created"
USER_UPDATED = "Users.Updated"
USER_ROLE_CHANGED = "Users.RoleChanged"

# APP settings
SECRET_KEY = "e8e2d862e49058382259f2e34a9d3854331c05c25b198b8cdc6a728ab24b3114"
# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=30)

# add SchemaRegistryValidator to the system path
sys.path.insert(0, "/mnt/d/work/Projects/async architecture/async_architecture/")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"task-manager": "Access to Task Manager Service", "accounting": "Access to Accounting Service"},
)
