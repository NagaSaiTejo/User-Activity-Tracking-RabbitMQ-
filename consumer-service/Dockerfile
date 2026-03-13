FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for cryptography / MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src

# We will run both the healthcheck API and the consumer process
# Using a simple shell script to start them both
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
