#!/bin/sh

# Start FastAPI healthcheck in the background
uvicorn src.main:app --host 0.0.0.0 --port 8001 &

# Start the consumer script in the foreground
python src/consumer.py
