import os
import pika
import json
import logging
import time
from datetime import datetime

from src.database import init_db, get_db, UserActivity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
QUEUE_NAME = "user_activity_events"

def process_message(ch, method, properties, body):
    logger.info(f"Received message: {body}")
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        data = json.loads(body)
        
        # Ensure timestamp is a datetime object
        timestamp_str = data.get('timestamp')
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            # Fallback or invalid format handling
            logger.warning(f"Invalid timestamp format: {timestamp_str}, using current time")
            timestamp = datetime.utcnow()

        new_activity = UserActivity(
            user_id=data.get('user_id'),
            event_type=data.get('event_type'),
            timestamp=timestamp,
            metadata_col=data.get('metadata')
        )
        
        db.add(new_activity)
        db.commit()
        logger.info(f"Successfully processed and stored event for user {new_activity.user_id}")
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode message JSON: {e}")
        # Reject message without requeueing (bad format)
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        db.rollback()
        # In a real system, you might retry or use a dead-letter queue. 
        # For resilience, we acknowledge to prevent an infinite loop of crashing if it's a poison pill, 
        # or we could nack with requeue=True for transient errors.
        # Requirements: "The Consumer Service MUST implement robust error handling... by logging the error and acknowledging the message"
        ch.basic_ack(delivery_tag=method.delivery_tag)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

def main():
    logger.info("Initializing database...")
    init_db()

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials
    )
    
    connection = None
    while not connection:
        try:
            connection = pika.BlockingConnection(parameters)
            logger.info("Successfully connected to RabbitMQ")
        except pika.exceptions.AMQPConnectionError:
            logger.warning("Failed to connect to RabbitMQ. Retrying in 5 seconds...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Fair dispatch
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
    
    logger.info('Waiting for messages. To exit press CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user.")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
