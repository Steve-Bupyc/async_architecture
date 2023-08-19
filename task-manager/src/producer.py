import json
import logging
from datetime import datetime
from uuid import uuid4

from aio_pika import DeliveryMode, ExchangeType, Message, connect_robust
from src.config import *

from schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


async def publish_message(event_data: dict, event_name: str, version: int, exchange: str) -> None:
    try:
        event_message = {
            "meta": {
                "id": str(uuid4()),
                "version": version,
                "name": event_name,
                "time": str(datetime.now()),
                "producer": "task-manager-service",
            },
            "data": event_data,
        }

        await SchemaRegistry.validate_event(event_message, event_name, version=version)

        await publish_message_to_rabbitmq_exchange(
            message_body=json.dumps(event_message),
            exchange_name=exchange,
            exchange_type=ExchangeType.TOPIC,
            routing_key=event_name,
        )
    except Exception:
        logger.exception(f"Failed to publish {event_name} message to {exchange} with data {event_message}")


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
