# FIAP X - Video Processing Platform - Architecture

## Overview

This project implements a microservices-based video processing platform with the following architecture:

```
                    ┌─────────────┐
                    │   Client    │
                    │  (Browser)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ API Gateway │
                    │  (Nginx)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌──▼───────┐ ┌──▼──────────┐
       │ Auth Service│ │  Video   │ │ Notification │
       │  (FastAPI)  │ │  Upload  │ │   Service    │
       │             │ │  Service │ │  (FastAPI)   │
       └──────┬──────┘ └──┬───────┘ └──────┬───────┘
              │            │                │
              │      ┌─────▼─────┐          │
              │      │ RabbitMQ  │          │
              │      │  (Queue)  │          │
              │      └─────┬─────┘          │
              │            │                │
              │      ┌─────▼─────┐          │
              │      │  Video    │          │
              │      │ Processing│          │
              │      │  Service  │          │
              │      └───────────┘          │
              │                             │
       ┌──────▼──────────────────────▼──────┐
       │         PostgreSQL + Redis          │
       └─────────────────────────────────────┘
                       │
                ┌──────▼──────┐
                │    MinIO    │
                │  (Storage)  │
                └─────────────┘
```

## Services

| Service | Technology | Port | Responsibility |
|---------|-----------|------|----------------|
| API Gateway | Nginx | 80 | Routing, rate limiting, JWT validation |
| Auth Service | FastAPI + PostgreSQL | 8001 | User registration, login, JWT tokens |
| Video Upload Service | FastAPI + MinIO + RabbitMQ | 8002 | Video upload, status management |
| Video Processing Service | FastAPI + RabbitMQ | 8003 | Concurrent video processing |
| Notification Service | FastAPI + RabbitMQ + SMTP | 8004 | Email notifications on errors |

## Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Message Broker | RabbitMQ | Async communication, peak handling |
| Database | PostgreSQL | Data persistence |
| Cache | Redis | Session/token cache, video status cache |
| Object Storage | MinIO | Video file storage (S3-compatible) |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Container Orchestration | Kubernetes (Minikube) | Scalability, orchestration |
| CI/CD | GitHub Actions | Automated testing and deployment |

## Key Design Decisions

1. **Asynchronous Processing**: Video uploads are decoupled from processing via RabbitMQ, ensuring no requests are lost during peak loads.

2. **Concurrent Processing**: The Video Processing Service uses worker pools to process multiple videos simultaneously.

3. **Authentication**: JWT-based authentication with bcrypt password hashing. Tokens are cached in Redis for fast validation.

4. **Scalability**: Each service can be independently scaled via Kubernetes replicas.

5. **Error Handling**: Failed video processing triggers notification events consumed by the Notification Service, which sends emails to users.

6. **Data Persistence**: PostgreSQL stores user data and video metadata/status. MinIO stores the actual video files.
