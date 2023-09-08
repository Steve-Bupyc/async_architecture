import asyncio
import json
import logging

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError
from src.config import *
from src.db.models import Task, Transaction, Types, User
from src.schemas import TaskCreateSchema, TaskUpdateSchema, TransactionCreateSchema, UserCreateSchema, UserUpdateSchema

from schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


async def users_consumer(message: AbstractIncomingMessage) -> None:
    async with message.process():
        data = json.loads(message.body.decode("utf-8"))
        logger.info(f"{message.routing_key} message received, body: {data}.")
        try:
            await SchemaRegistry.validate_event(data, message.routing_key, version=data["meta"]["version"])
        except ValidationError:
            logger.exception(f"{message.routing_key} message is invalid.")
            return

        if message.routing_key == USER_CREATED:
            await User.create(UserCreateSchema.model_validate(data["data"]))
        elif message.routing_key == USER_UPDATED:
            await User.update(data["data"]["guid"], UserUpdateSchema.model_validate(data["data"]))
        elif message.routing_key == USER_ROLE_CHANGED:
            await User.update_role(data["data"]["guid"], data["data"]["role"])


async def tasks_consumer(message: AbstractIncomingMessage) -> None:
    async with message.process():
        data = json.loads(message.body.decode("utf-8"))
        logger.info(f"{message.routing_key} message received, body: {data}.")
        try:
            await SchemaRegistry.validate_event(data, message.routing_key, version=data["meta"]["version"])
        except ValidationError:
            logger.exception(f"{message.routing_key} message is invalid.")
            return

        if message.routing_key == TASK_ADDED:
            db_task = await Task.create(TaskCreateSchema.model_validate(data["data"]))
            await Transaction.create(
                TransactionCreateSchema(
                    user_guid=db_task.assigned_to,
                    amount=db_task.price,
                    description=f"Снятие за таску {db_task.title} [{db_task.jira_id}]",
                    type=Types.credit,
                )
            )
            await User.update_balance(db_task.assigned_to, -db_task.price)
        elif message.routing_key == TASK_UPDATED:
            await Task.update(data["data"]["guid"], TaskUpdateSchema.model_validate(data["data"]))
        elif message.routing_key == TASK_ASSIGNED:
            db_task = await Task.assign(data["data"]["guid"], data["data"]["assigned_to"])
            await Transaction.create(
                TransactionCreateSchema(
                    user_guid=db_task.assigned_to,
                    amount=db_task.price,
                    description=f"Снятие за таску {db_task.title} [{db_task.jira_id}]",
                    type=Types.credit,
                )
            )
            await User.update_balance(db_task.assigned_to, -db_task.price)
        elif message.routing_key == TASK_COMPLETED:
            db_task = await Task.get(data["data"]["guid"])
            await Transaction.create(
                TransactionCreateSchema(
                    user_guid=db_task.assigned_to,
                    amount=db_task.reward,
                    description=f"Пополнение за таску {db_task.title} [{db_task.jira_id}]",
                    type=Types.debit,
                )
            )
            await User.update_balance(db_task.assigned_to, db_task.reward)


async def worker() -> None:
    # Perform connection
    connection = await connect_robust(RABBITMQ_SERVICE_URL)
    async with connection:
        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declare an exchange
        users_stream_exchange = await channel.declare_exchange(USERS_STREAM_EXCHANGE, ExchangeType.TOPIC, durable=True)
        users_lifecycle_exchange = await channel.declare_exchange(
            USERS_LIFECYCLE_EXCHANGE, ExchangeType.TOPIC, durable=True
        )
        tasks_stream_exchange = await channel.declare_exchange(TASKS_STREAM_EXCHANGE, ExchangeType.TOPIC, durable=True)
        tasks_lifecycle_exchange = await channel.declare_exchange(
            TASKS_LIFECYCLE_EXCHANGE, ExchangeType.TOPIC, durable=True
        )

        # Declaring queue
        user_stream_queue = await channel.declare_queue("accounting.user-stream.queue", durable=True)
        users_lifecycle_queue = await channel.declare_queue("accounting.user-lifecycle.queue", durable=True)
        tasks_stream_queue = await channel.declare_queue("accounting.tasks-stream.queue", durable=True)
        tasks_lifecycle_queue = await channel.declare_queue("accounting.tasks-lifecycle.queue", durable=True)

        await user_stream_queue.bind(users_stream_exchange, routing_key=USER_CREATED)
        await user_stream_queue.bind(users_stream_exchange, routing_key=USER_UPDATED)
        await users_lifecycle_queue.bind(users_lifecycle_exchange, routing_key=USER_ROLE_CHANGED)
        await tasks_stream_queue.bind(tasks_stream_exchange, routing_key=TASK_CREATED)
        await tasks_stream_queue.bind(tasks_stream_exchange, routing_key=TASK_UPDATED)
        await tasks_lifecycle_queue.bind(tasks_lifecycle_exchange, routing_key=TASK_ADDED)
        await tasks_lifecycle_queue.bind(tasks_lifecycle_exchange, routing_key=TASK_ASSIGNED)
        await tasks_lifecycle_queue.bind(tasks_lifecycle_exchange, routing_key=TASK_COMPLETED)

        await user_stream_queue.consume(users_consumer)
        await users_lifecycle_queue.consume(users_consumer)
        await tasks_stream_queue.consume(tasks_consumer)
        await tasks_lifecycle_queue.consume(tasks_consumer)
        logger.info(" [*] Waiting for messages.")
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.debug("=== Starting the consumer ===")
    asyncio.run(worker())
