import json
import logging

from aio_pika import DeliveryMode, ExchangeType, Message, connect_robust

from src.config import *

logger = logging.getLogger(__name__)


async def publish_message(data: dict, routing_key: str = "", exchange: str = "user.topic") -> None:
    try:
        await publish_message_to_rabbitmq_exchange(
            message_body=json.dumps({"data": data}),
            exchange_name=exchange,
            exchange_type=ExchangeType.TOPIC,
            routing_key=routing_key,
        )
    except Exception:
        logger.exception(f"Failed to publish {routing_key} message to {exchange} with data {data}")


async def publish_message_to_rabbitmq_exchange(
    message_body: json, exchange_name: str, exchange_type: str, routing_key: str
) -> None:
    logger.info(f"Trying to publish to '{exchange_name}' with '{routing_key}'")
    connection = await connect_robust(RABBITMQ_SERVICE_URL)
    try:
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(exchange_name, exchange_type, durable=True)
            message_body = message_body

            message = Message(
                message_body.encode("utf-8"), content_type="application/json", delivery_mode=DeliveryMode.PERSISTENT
            )

            await exchange.publish(message, routing_key=routing_key)
    except Exception:
        logger.exception(f"Failed to publish to '{exchange_name}' with '{routing_key}', body: {message_body}")
    else:
        logger.info(f"Published to '{exchange_name}' with '{routing_key}', body: {message_body}")
