from sqlalchemy import UUID, Boolean, Column, Enum, Integer, String, func
from src.config import *
from src.db.base import Base, Roles, db
from src.producer import publish_message
from src.schemas import UserCreateSchema, UserUpdateSchema


class User(Base):
    __tablename__ = "user"

    id = Column("id", Integer, primary_key=True)
    guid = Column("guid", UUID(as_uuid=True), unique=True, server_default=func.gen_random_uuid())
    username = Column("username", String, nullable=False, unique=True)
    password = Column("password", String, nullable=False)
    full_name = Column("full_name", String)
    role = Column("role", Enum(Roles, inherit_schema=True), nullable=False)
    is_active = Column("is_active", Boolean, default=True, nullable=False)

    @classmethod
    async def authenticate(self, username: str, password: str):
        user = await self.get_by_email(username)
        if not user:
            return False

        if not self._verify_password(password, user.password):
            return False

        return user

    @classmethod
    async def create(self, user: UserCreateSchema):
        setattr(user, "password", self._get_password_hash(user.password))
        db_user = User()
        for key in user.model_fields:
            setattr(db_user, key, getattr(user, key))
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        await publish_message(
            {
                "guid": str(db_user.guid),
                "username": db_user.username,
                "full_name": db_user.full_name,
                "role": db_user.role,
                "is_active": db_user.is_active,
            },
            "users.created",
            1,
            USERS_CUD_EVENTS_EXCHANGE,
        )

        return db_user

    @classmethod
    async def update(self, guid: UUID, user: UserUpdateSchema):
        db_user = db.query(self).filter(self.guid == guid).first()
        role_changed = False
        for key in user.model_fields:
            new_value = getattr(user, key)
            if new_value is not None:
                cur_value = getattr(db_user, key)
                if new_value != cur_value:
                    if key == "role":
                        role_changed = True

                    setattr(db_user, key, new_value)

        db.commit()
        db.refresh(db_user)

        await publish_message(
            {
                "guid": str(db_user.guid),
                "username": db_user.username,
                "full_name": db_user.full_name,
                "role": db_user.role,
                "is_active": db_user.is_active,
            },
            "users.updated",
            1,
            USERS_CUD_EVENTS_EXCHANGE,
        )
        BUSINESS_EVENTS_EXCHANGE
        if role_changed:
            await publish_message(
                {"guid": str(db_user.guid), "role": db_user.role},
                "users.role_changed",
                1,
                BUSINESS_EVENTS_EXCHANGE,
            )

        return db_user

    @classmethod
    async def get(self, guid: UUID):
        return db.query(self).filter(self.guid == guid).first()

    @classmethod
    async def get_by_email(self, username: str):
        return db.query(self).filter(self.username == username).first()

    @staticmethod
    def _verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def _get_password_hash(password):
        return pwd_context.hash(password)
