import asyncio
import json
import logging

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError
from src.config import *
from src.db.models import User
from src.schemas import (
    UserCreatedRabbitSchema,
    UserCreateSchema,
    UserRoleChangedRabbitSchema,
    UserUpdatedRabbitSchema,
    UserUpdateSchema,
)

logger = logging.getLogger(__name__)


ROUTING_KEY_TO_VALIDATION_SCHEME_MAPPING = {
    USER_CREATED: UserCreatedRabbitSchema,
    USER_UPDATED: UserUpdatedRabbitSchema,
    USER_ROLE_CHANGED: UserRoleChangedRabbitSchema,
}


async def consumer(message: AbstractIncomingMessage) -> None:
    async with message.process():
        body = json.loads(message.body.decode("utf-8"))
        logger.info(f"{message.routing_key} message received, body: {body}.")
        try:
            validation_scheme = ROUTING_KEY_TO_VALIDATION_SCHEME_MAPPING[message.routing_key]
            model = validation_scheme.model_validate(body["data"])
        except ValidationError:
            logger.exception(f"{message.routing_key} message is invalid.")
            return

        if message.routing_key == USER_CREATED:
            await User.create(UserCreateSchema.model_validate(model.model_dump()))
        elif message.routing_key == USER_UPDATED:
            await User.update(model.guid, UserUpdateSchema.model_validate(model.model_dump()))
        elif message.routing_key == USER_UPDATED:
            await User.update_role(model.guid, model.role)


async def worker() -> None:
    # Perform connection
    connection = await connect_robust(RABBITMQ_SERVICE_URL)
    async with connection:
        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declare an exchange
        user_exchange = await channel.declare_exchange("user.topic", ExchangeType.TOPIC, durable=True)

        # Declaring queue
        payment_queue = await channel.declare_queue(
            "task-manager.user.queue",
            durable=True,
        )

        await payment_queue.bind(user_exchange, routing_key=USER_CREATED)
        await payment_queue.bind(user_exchange, routing_key=USER_UPDATED)
        await payment_queue.bind(user_exchange, routing_key=USER_ROLE_CHANGED)

        await payment_queue.consume(consumer)
        logger.info(" [*] Waiting for messages.")
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.debug("=== Starting the consumer ===")
    asyncio.run(worker())
