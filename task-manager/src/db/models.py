from sqlalchemy import UUID, Boolean, Column, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from src.db.base import Base, Roles, db
from src.schemas import TaskCreateSchema, UserCreateSchema, UserUpdateSchema

from schema_registry import SchemaRegistry


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    guid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    role = Column(Enum(Roles, inherit_schema=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_tasks = relationship("Task", back_populates="created", foreign_keys="Task.created_by")
    assigned_tasks = relationship("Task", back_populates="assigned", foreign_keys="Task.assigned_to")

    @classmethod
    async def create(self, user: UserCreateSchema):
        db_user = User(guid=user.guid, username=user.username, full_name=user.full_name, role=user.role)
        db.add(db_user)
        db.commit()

    @classmethod
    async def update(self, guid: UUID, user: UserUpdateSchema):
        db_user = db.query(self).filter(self.guid == guid).first()
        for key in user.model_fields:
            new_value = getattr(user, key)
            if new_value is not None:
                cur_value = getattr(db_user, key)
                if new_value != cur_value:
                    setattr(db_user, key, new_value)

        db.commit()

    @classmethod
    async def update_role(self, guid: UUID, role: Roles):
        db_user = db.query(self).filter(self.guid == guid).first()
        db_user.role = role

        db.commit()

    @classmethod
    async def get(self, guid: UUID):
        return db.query(self).filter(self.guid == guid).first()

    @classmethod
    async def get_by_username(self, username: str):
        return db.query(self).filter(self.username == username).first()


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    guid = Column(UUID(as_uuid=True), server_default=func.gen_random_uuid())
    title = Column(String, nullable=False)
    description = Column(String)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.guid"), index=True, nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("user.guid"), index=True, nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)

    created = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    assigned = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")

    @classmethod
    async def create(self, task: TaskCreateSchema, created_by: UUID):
        assigned_user = (
            db.query(User).filter(User.role.not_in([Roles.manager, Roles.admin])).order_by(func.random()).first()
        )

        db_task = Task(created_by=created_by, assigned_to=assigned_user.guid)
        for key in task.model_fields:
            setattr(db_task, key, getattr(task, key))
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        await SchemaRegistry.validate_event({"test": 1}, "users.created", 1)

        return db_task

    @classmethod
    async def update(self, guid: UUID, user: UserUpdateSchema):
        db_user = db.query(self).filter(self.guid == guid).first()
        for key in user.model_fields:
            new_value = getattr(user, key)
            if new_value is not None:
                cur_value = getattr(db_user, key)
                if new_value != cur_value:
                    setattr(db_user, key, new_value)

        db.commit()
        db.refresh(db_user)

        return db_user

    @classmethod
    async def get(self, guid: UUID):
        return db.query(self).filter(self.guid == guid).first()
