from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any
import logging

from src.schemas import UserActivityEvent
from src.rabbitmq import publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Event-Driven User Activity Tracking API")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.on_event("startup")
def startup_event():
    try:
        publisher.connect()
    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ on startup: {e}")

@app.on_event("shutdown")
def shutdown_event():
    publisher.close()

@app.post("/api/v1/events/track", status_code=status.HTTP_202_ACCEPTED)
async def track_event(event: UserActivityEvent) -> Any:
    try:
        # Convert datetime to ISO format string for JSON serialization
        event_dict = event.model_dump()
        event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        
        publisher.publish_event(event_dict)
        return {"message": "Event accepted"}
        
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Could not process event"}
        )

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    health_status = {"status": "ok", "rabbitmq": "connected"}
    
    if not publisher.connection or publisher.connection.is_closed:
        try:
             publisher.connect(retries=1, delay=1)
        except Exception:
             health_status["rabbitmq"] = "disconnected"
             return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)

    return health_status
