import os
import pika
import json
import logging
import time

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
QUEUE_NAME = "user_activity_events"

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self, retries=5, delay=5):
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        
        for attempt in range(1, retries + 1):
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=QUEUE_NAME, durable=True)
                logger.info("Successfully connected to RabbitMQ")
                return
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Connection attempt {attempt} failed: {e}")
                if attempt < retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("Failed to connect to RabbitMQ after multiple attempts.")
                    raise

    def publish_event(self, event_data: dict):
        if not self.connection or self.connection.is_closed:
            self.connect()

        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(event_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            raise

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")

publisher = RabbitMQPublisher()
