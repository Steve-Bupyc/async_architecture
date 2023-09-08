import asyncio
import json
import logging

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError
from src.config import *
from src.db.models import User
from src.schemas import UserCreateSchema, UserUpdateSchema

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

        # Declaring queue
        user_stream_queue = await channel.declare_queue("task-manager.user-stream.queue", durable=True)
        users_lifecycle_queue = await channel.declare_queue("task-manager.user-lifecycle.queue", durable=True)

        await user_stream_queue.bind(users_stream_exchange, routing_key=USER_CREATED)
        await user_stream_queue.bind(users_stream_exchange, routing_key=USER_UPDATED)
        await users_lifecycle_queue.bind(users_lifecycle_exchange, routing_key=USER_ROLE_CHANGED)

        await user_stream_queue.consume(users_consumer)
        await users_lifecycle_queue.consume(users_consumer)
        logger.info(" [*] Waiting for messages.")
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.debug("=== Starting the consumer ===")
    asyncio.run(worker())
