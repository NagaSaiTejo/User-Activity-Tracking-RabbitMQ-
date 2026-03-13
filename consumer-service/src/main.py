from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import pika
import os
import logging

from src.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Event-Driven Consumer Health Check API")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

def check_rabbitmq():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        return True
    except Exception as e:
        logger.error(f"RabbitMQ Healthcheck failed: {e}")
        return False

def check_database():
    try:
        with engine.connect() as connection:
            return True
    except Exception as e:
        logger.error(f"Database Healthcheck failed: {e}")
        return False

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    rabbit_ok = check_rabbitmq()
    db_ok = check_database()
    
    health_status = {
        "status": "ok" if rabbit_ok and db_ok else "error",
        "rabbitmq": "connected" if rabbit_ok else "disconnected",
        "database": "connected" if db_ok else "disconnected"
    }
    
    if not rabbit_ok or not db_ok:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)

    return health_status
