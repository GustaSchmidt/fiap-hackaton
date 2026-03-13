import json
import logging

import pika

from app.config import settings

logger = logging.getLogger(__name__)


def get_rabbitmq_connection():
    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    parameters.connection_attempts = 5
    parameters.retry_delay = 5
    return pika.BlockingConnection(parameters)


def publish_video_event(event_type: str, video_data: dict):
    """Publish a video event to RabbitMQ.

    event_type: 'video.uploaded', 'video.processing', 'video.completed', 'video.error'
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()

        channel.exchange_declare(
            exchange="video_events", exchange_type="topic", durable=True
        )

        message = json.dumps(
            {
                "event_type": event_type,
                "data": video_data,
            }
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
        logger.error(f"Failed to publish event: {e}")
        return False
