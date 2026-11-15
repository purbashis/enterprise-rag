---
name: system-architecture
description: Multi-agent AI system architecture for the RAG application
metadata:
  type: reference
---

# Multi-Agent AI System Architecture

## Agent Overview

The system consists of specialized microservices communicating via an event-driven architecture:

### 1. Web Browsing Agent
- **Purpose**: Real-time information retrieval and research
- **Tools**: Playwright/Selenium for web navigation, API calling
- **Memory**: Long-term context storage in Redis
- **Output**: Structured research findings with source citations

### 2. API Tool-Calling Agent
- **Purpose**: Execute arbitrary API calls, integrate external services
- **Tools**: HTTP client, JSON schema validation, response parsing
- **Memory**: Session-based state management
- **Output**: API response data formatted for downstream consumers

### 3. Long-Term Memory Agent
- **Purpose**: Persistent knowledge storage, recall, and context maintenance
- **Tools**: Vector store (FAISS), Redis for semantic caching, JSON persistence
- **Memory**: Vector embeddings + key-value store for conversation history
- **Output**: Retrieved context, conversation summaries, persistent state

### 4. RAG Orchestration Agent
- **Purpose**: Coordinate document processing, query routing, model selection
- **Tools**: LangChain chains, model factory, document services
- **Memory**: FAISS vector store, document metadata tracking
- **Output**: Answer with sources, document management operations

## Communication Pattern

```
Web Browser Agent ←→ API Gateway ←→ RAG Orchestration ←→ Memory Agent
           ↑                          ↑
           └───────────━━━━━━━━━━━━━━━━━━━━┛
```

## Docker Deployment

Each agent runs in its own container with:
- Isolated Python environments
- Shared volume for data persistence
- Health checks and restart policies
- Environment-based configuration

## AWS Deployment

- **ECR**: Container images stored in Amazon Elastic Container Registry
- **ECS/Fargate**: Serverless container orchestration
- **ALB**: Application Load Balancer for high availability
- **CloudWatch**: Monitoring, logging, and metrics
- **ACM**: SSL/TLS certificate management