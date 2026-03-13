# Event-Driven User Activity Tracking Service

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

## 📝 Overview
A robust, distributed backend system for high-throughput tracking of user activities (login, logout, page views). This architecture utilizes **RabbitMQ** to decouple the API entry point from the persistence layer, ensuring system resilience and scalability.

## 🏗️ Architecture
The system is composed of four containerized components:

1.  **Producer Service (FastAPI):** Validates incoming `UserActivityEvent` payloads and publishes them to the queue. Returns `202 Accepted` to minimize client-side latency.
2.  **Message Broker (RabbitMQ):** Manages the asynchronous event queue (`user_activity_events`) with message persistence enabled.
3.  **Consumer Service (Python/SQLAlchemy):** Subscribes to the queue, processes events, and handles MySQL transactions. Includes robust error handling to prevent message loss.
4.  **Database (MySQL):** Stores activity logs in the `user_activities` table with support for JSON metadata.

---

## 🚀 Setup and Installation

### Prerequisites
- [Docker & Docker Compose](https://docs.docker.com/get-docker/)

### 1. Configuration
Initialize the environment variables:
```bash
cp .env.example .env
```

### 2. Deployment
Start all services in detached mode:
```bash
docker-compose up -d --build
```

### 3. Health Verification
Verify that all services are operational and connected:
- **Producer Health:** `curl http://localhost:8000/health`
- **Consumer Health:** `curl http://localhost:8001/health`

---

## 📡 API Usage

### Track Activity
`POST /api/v1/events/track`

**Sample Request Body:**
```json
{
  "user_id": 123,
  "event_type": "page_view",
  "timestamp": "2023-10-27T10:00:00Z",
  "metadata": {
    "page_url": "/products/item-xyz",
    "session_id": "abc123"
  }
}
```

**Response Codes:**
- `202 Accepted`: Event successfully queued for processing.
- `400 Bad Request`: Payload validation error (handled by custom FastAPI exception handlers).
- `500 Server Error`: Internal system failure.

---

## 🧪 Testing and Validation

### Automated Suites
Execute unit and integration tests inside the running containers:
```bash
# Test Producer Service
docker-compose exec producer-service pytest tests/

# Test Consumer Service
docker-compose exec consumer-service pytest tests/
```

### Manual Database Check
Verify event persistence directly in MySQL:
```bash
docker-compose exec mysql mysql -uroot -proot_password user_activity_db -e "SELECT * FROM user_activities;"
```

---

## 🛠️ Technical Implementation Details

- **Decoupling:** The Producer never interacts with the database, protecting the API from DB latency or outages.
- **Reliability:** Messages are set to `delivery_mode=2` (persistent) and queues are `durable`. Consumers use manual ACKs to ensure no message is lost.
- **Failover:** Both services implement exponential backoff retry logic for RabbitMQ and Database connections.
- **Schema Validation:** Pydantic models ensure strict data integrity at the API gateway.

---

## 👨‍💼 Business Impact (Stakeholder Summary)
By moving from a synchronous to an **Event-Driven Architecture**, we eliminate the risk of database performance impacting the end-user experience. This system acts as a high-capacity "buffer," allowing the application to handle massive traffic spikes without data loss or service degradation. It is a future-proof foundation for real-time analytics and auditing.
