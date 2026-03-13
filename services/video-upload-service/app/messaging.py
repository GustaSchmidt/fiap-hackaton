import json
import logging
import time

import pika

from app.config import settings

logger = logging.getLogger(__name__)

MAX_PUBLISH_RETRIES = 3
PUBLISH_RETRY_DELAY = 2


def get_rabbitmq_connection():
    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    parameters.connection_attempts = 5
    parameters.retry_delay = 5
    return pika.BlockingConnection(parameters)


def publish_video_event(event_type: str, video_data: dict):
    """Publish a video event to RabbitMQ with retry logic.

    event_type: 'video.uploaded', 'video.processing', 'video.completed', 'video.error'

    Retries up to MAX_PUBLISH_RETRIES times on failure to ensure the message
    reaches the queue even under transient connectivity issues.
    """
    message = json.dumps(
        {
            "event_type": event_type,
            "data": video_data,
        }
    )

    last_error = None
    for attempt in range(1, MAX_PUBLISH_RETRIES + 1):
        try:
            connection = get_rabbitmq_connection()
            channel = connection.channel()

            channel.exchange_declare(
                exchange="video_events", exchange_type="topic", durable=True
            )

            channel.basic_publish(
                exchange="video_events",
                routing_key=event_type,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent message
                    content_type="application/json",
                ),
            )

            connection.close()
            logger.info(f"Published event {event_type} for video {video_data.get('video_id')}")
            return True
        except Exception as e:
            last_error = e
            logger.warning(
                f"Attempt {attempt}/{MAX_PUBLISH_RETRIES} failed to publish "
                f"event {event_type}: {e}"
            )
            if attempt < MAX_PUBLISH_RETRIES:
                time.sleep(PUBLISH_RETRY_DELAY)

    logger.error(
        f"Failed to publish event {event_type} after {MAX_PUBLISH_RETRIES} "
        f"attempts: {last_error}"
    )
    return False
