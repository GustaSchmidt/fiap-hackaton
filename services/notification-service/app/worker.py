import json
import logging

import httpx
import pika

from app.config import settings
from app.notifier import send_error_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_user_email(user_id: int) -> str:
    """Fetch user email from the auth service."""
    try:
        # For internal service communication, we use a direct endpoint
        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/health",
            timeout=5,
        )
        # In production, this would call a proper internal endpoint
        # For now, return a default email for demo purposes
        return f"user_{user_id}@fiapx.com"
    except Exception as e:
        logger.error(f"Failed to fetch user email for user {user_id}: {e}")
        return f"user_{user_id}@fiapx.com"


def callback(ch, method, properties, body):
    """RabbitMQ callback for video.error events."""
    try:
        message = json.loads(body)
        event_type = message.get("event_type")
        data = message.get("data", {})

        logger.info(f"Received event: {event_type}")

        if event_type == "video.error":
            user_id = data.get("user_id")
            video_name = data.get("original_filename", "Unknown")
            error_message = data.get("error_message", "Erro desconhecido")

            user_email = get_user_email(user_id)
            send_error_notification(user_email, video_name, error_message)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing notification message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_worker():
    """Start consuming error events from RabbitMQ."""
    logger.info("Starting Notification Worker...")

    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    parameters.connection_attempts = 10
    parameters.retry_delay = 5

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(
        exchange="video_events", exchange_type="topic", durable=True
    )

    channel.queue_declare(queue="notification_queue", durable=True)
    channel.queue_bind(
        exchange="video_events",
        queue="notification_queue",
        routing_key="video.error",
    )

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue="notification_queue",
        on_message_callback=callback,
    )

    logger.info("Notification Worker is ready. Waiting for error events...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
