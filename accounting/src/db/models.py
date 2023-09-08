from random import randint

from sqlalchemy import UUID, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from src.config import *
from src.db.base import Base, PaymentStatuses, Roles, Types, db
from src.producer import publish_message
from src.schemas import TaskCreateSchema, TaskUpdateSchema, TransactionCreateSchema, UserCreateSchema, UserUpdateSchema


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    guid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    role = Column(Enum(Roles, inherit_schema=True), nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    assigned_tasks = relationship("Task", back_populates="assigned", foreign_keys="Task.assigned_to")
    transactions = relationship("Transaction", back_populates="user", foreign_keys="Transaction.user_guid")

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
        db_user = await self.get(guid)
        db_user.role = role

        db.commit()

    @classmethod
    async def update_balance(self, guid: UUID, amount: int):
        db_user = await self.get(guid)
        db_user.balance = db_user.balance + amount

        db.commit()

    @classmethod
    async def reset_balance(self, guid: UUID):
        db_user = await self.get(guid)
        db_user.balance = 0

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
    guid = Column(UUID(as_uuid=True), unique=True)
    title = Column(String, nullable=False)
    jira_id = Column(String, nullable=False)
    description = Column(String)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("user.guid"), index=True, nullable=False)
    price = Column(Integer, nullable=False)
    reward = Column(Integer, nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)

    assigned = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")

    @classmethod
    async def create(self, task: TaskCreateSchema):
        price = randint(10, 20)
        reward = randint(20, 40)
        db_task = Task(price=price, reward=reward)
        for key in task.model_fields:
            setattr(db_task, key, getattr(task, key))
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        return db_task

    @classmethod
    async def update(self, guid: UUID, task: TaskUpdateSchema):
        db_task = await self.get(guid)
        for key in task.model_fields:
            new_value = getattr(task, key)
            if new_value is not None:
                cur_value = getattr(db_task, key)
                if new_value != cur_value:
                    setattr(db_task, key, new_value)

        db.commit()

    @classmethod
    async def assign(self, task_guid: UUID, user_guid: UUID):
        db_task = await self.get(task_guid)
        db_task.assigned_to = user_guid
        db.commit()
        db.refresh(db_task)

        return db_task

    @classmethod
    async def get(self, guid: UUID):
        return db.query(self).filter(self.guid == guid).first()


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True)
    guid = Column(UUID(as_uuid=True), unique=True, server_default=func.gen_random_uuid())
    user_guid = Column(UUID(as_uuid=True), ForeignKey("user.guid"), index=True, nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(Enum(Types, inherit_schema=True), nullable=False)
    description = Column(String)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_guid], back_populates="transactions")
    payment = relationship("Payment", back_populates="transaction", foreign_keys="Payment.transaction_guid")

    @classmethod
    async def create(self, transaction: TransactionCreateSchema):
        db_transaction = Transaction()
        for key in transaction.model_fields:
            setattr(db_transaction, key, getattr(transaction, key))
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        return db_transaction

    @classmethod
    async def get(self, guid: UUID):
        return db.query(self).filter(self.guid == guid).first()


class Payment(Base):
    __tablename__ = "payment"
    id = Column(Integer, primary_key=True)
    guid = Column(UUID(as_uuid=True), unique=True, server_default=func.gen_random_uuid())
    amount = Column(Integer, nullable=False)
    status = Column(Enum(PaymentStatuses, inherit_schema=True), nullable=False, default=PaymentStatuses.created)
    transaction_guid = Column(UUID(as_uuid=True), ForeignKey("transaction.guid"), index=True, nullable=False)

    transaction = relationship("Transaction", back_populates="payment", foreign_keys=[transaction_guid])

    @classmethod
    async def create(self, transaction_guid: UUID, amount: int):
        db_payment = Payment(amount=amount, transaction_guid=transaction_guid)
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)

        await publish_message(
            {"guid": str(db_payment.guid), "amount": db_payment.amount}, PAYMENTS_SENT, 1, PAYMENT_LIFECYCLE_EXCHANGE
        )
        return db_payment
