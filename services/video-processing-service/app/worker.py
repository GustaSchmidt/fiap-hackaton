import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

import httpx
import pika

from app.config import settings
from app.processor import process_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_WORKERS)


def update_video_status(video_id: int, status: str, error_message: str = None):
    """Update video status via the upload service API."""
    try:
        payload = {"status": status}
        if error_message:
            payload["error_message"] = error_message

        response = httpx.patch(
            f"{settings.VIDEO_UPLOAD_SERVICE_URL}/videos/{video_id}/status",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Updated video {video_id} status to '{status}'")
    except Exception as e:
        logger.error(f"Failed to update video {video_id} status: {e}")


def publish_error_event(connection_params, video_data: dict, error_message: str):
    """Publish error event for notification service."""
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.exchange_declare(
            exchange="video_events", exchange_type="topic", durable=True
        )

        message = json.dumps(
            {
                "event_type": "video.error",
                "data": {
                    **video_data,
                    "error_message": error_message,
                },
            }
        )

        channel.basic_publish(
            exchange="video_events",
            routing_key="video.error",
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish error event: {e}")


def handle_video(video_data: dict, connection_params):
    """Process a single video in a thread."""
    video_id = video_data["video_id"]
    filename = video_data["filename"]

    # Update status to processing
    update_video_status(video_id, "processing")

    # Process the video
    success = process_video(video_id, filename)

    if success:
        update_video_status(video_id, "completed")
        logger.info(f"Video {video_id} processed successfully")
    else:
        error_msg = "Video processing failed"
        update_video_status(video_id, "error", error_msg)
        publish_error_event(connection_params, video_data, error_msg)
        logger.error(f"Video {video_id} processing failed")


def callback(ch, method, properties, body):
    """RabbitMQ callback for video.uploaded events."""
    try:
        message = json.loads(body)
        event_type = message.get("event_type")
        video_data = message.get("data", {})

        logger.info(f"Received event: {event_type} for video {video_data.get('video_id')}")

        if event_type == "video.uploaded":
            # Update status to queued
            update_video_status(video_data["video_id"], "queued")

            # Submit to thread pool for concurrent processing
            connection_params = pika.URLParameters(settings.RABBITMQ_URL)
            executor.submit(handle_video, video_data, connection_params)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_worker():
    """Start consuming messages from RabbitMQ."""
    logger.info("Starting Video Processing Worker...")
    logger.info(f"Max concurrent workers: {settings.MAX_CONCURRENT_WORKERS}")

    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    parameters.connection_attempts = 10
    parameters.retry_delay = 5

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(
        exchange="video_events", exchange_type="topic", durable=True
    )

    queue = channel.queue_declare(queue="video_processing_queue", durable=True)
    channel.queue_bind(
        exchange="video_events",
        queue="video_processing_queue",
        routing_key="video.uploaded",
    )

    # Prefetch count limits concurrent messages per consumer
    channel.basic_qos(prefetch_count=settings.MAX_CONCURRENT_WORKERS)

    channel.basic_consume(
        queue="video_processing_queue",
        on_message_callback=callback,
    )

    logger.info("Worker is ready. Waiting for video events...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
