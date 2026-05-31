# Agentic AI Workflow Orchestrator

A production-style backend platform where multiple AI agents collaborate to solve complex workflows using planning, execution, validation, retry logic, memory, and asynchronous processing.

## Project Overview

This project implements an agentic workflow orchestration system using FastAPI, LangGraph, Redis, PostgreSQL, and Docker.

A user submits a high-level workflow goal through an API. The system stores the workflow in PostgreSQL, pushes the workflow ID to Redis, and a background worker processes the task asynchronously using a LangGraph-based multi-agent pipeline.

The workflow includes:

- Planner Agent
- Executor Agent
- Validator Agent
- Memory Agent
- Dynamic routing
- Retry logic
- Short-term memory
- Persistent workflow logs

## Tech Stack

- Python
- FastAPI
- LangGraph
- Redis
- PostgreSQL
- Docker
- Docker Compose
- asyncpg
- Pydantic
- Gemini API
- google-genai

## Architecture

```text
User
 |
 | POST /workflows
 v
FastAPI API Service
 |
 | Save workflow
 v
PostgreSQL
 |
 | Push workflow event
 v
Redis Stream
 |
 | Consume event
 v
Worker Service
 |
 | Run LangGraph workflow
 v
Planner Agent
 |
 v
Executor Agent
 |
 v
Validator Agent
 |
 | if validation fails
 +------ retry executor
 |
 | if validation passes
 v
Memory Agent
 |
 v
PostgreSQL stores final result
```

## Agent Flow

### 1. Planner Agent

The planner agent receives the user goal and breaks it into structured steps.

### 2. Executor Agent

The executor agent performs the actual task using tools. In Version 2, the executor uses Gemini-powered tools for research generation and structured summarization.

### 3. Validator Agent

The validator agent checks whether the output is valid. If validation fails, the workflow is routed back to the executor agent for retry.

### 4. Memory Agent

The memory agent stores short-term workflow context in Redis.

## LLM Integration

Version 2 integrates Gemini LLM into the tool layer.

The executor agent uses Gemini-powered tools for:

- Research generation
- Structured summarization

The project also includes fallback handling. If Gemini fails because of quota limits, API key issues, timeout, or network problems, the system falls back to deterministic local responses so the workflow can still complete.

This makes the orchestration system more reliable and production-friendly.

## Why This Project Is Agentic

This is not a simple sequential pipeline. The workflow uses shared state, specialized agents, conditional routing, validation feedback, memory, and retry logic.

The validator can dynamically decide whether the output should be accepted or whether the executor should retry.

## API Endpoints

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Create Workflow

```http
POST /workflows
```

Request body:

```json
{
  "goal": "Create a market research summary on electric vehicles in India"
}
```

Response:

```json
{
  "workflow_id": 1,
  "status": "PENDING",
  "result": null
}
```

### Get Workflow Result

```http
GET /workflows/{workflow_id}
```

Example response:

```json
{
  "workflow_id": 1,
  "goal": "Create a market research summary on electric vehicles in India",
  "status": "COMPLETED",
  "result": {
    "goal": "Create a market research summary on electric vehicles in India",
    "plan": [
      "Understand the user goal",
      "Collect useful information",
      "Generate a clear final summary",
      "Validate the final summary",
      "Store the final workflow memory"
    ],
    "final_answer": "Final Summary: ...",
    "validation_passed": true,
    "retry_count": 0
  },
  "error": null
}
```

## How to Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Archit02-boop/Agentic-AI-Workflow-orchestrator.git
cd Agentic-AI-Workflow-orchestrator
```

### 2. Create `.env`

Create a `.env` file using `.env.example`:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/orchestrator
REDIS_URL=redis://redis:6379/0
WORKFLOW_STREAM=workflow_stream
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run with Docker

```bash
docker compose up --build
```

The system will start:

- FastAPI API service
- Worker service
- PostgreSQL
- Redis

### 4. Open API Docs

```text
http://localhost:8000/docs
```

## Example Test Using PowerShell

Create a workflow:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/workflows" -ContentType "application/json" -Body '{"goal":"Create a market research summary on electric vehicles in India"}'
```

Get workflow result:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/workflows/1"
```

## Key Features

- Multi-agent orchestration
- Gemini-powered execution tools
- Dynamic task routing
- Validation-based retry loop
- LLM fallback handling
- Asynchronous workflow execution
- Redis Stream event queue
- PostgreSQL persistence
- Agent execution logs
- Dockerized microservice setup
- Short-term workflow memory

## Database Tables

### workflows

Stores workflow goal, status, result, error, and timestamps.

### agent_logs

Stores each agent's input and output for observability and debugging.


## Future Improvements

- Add support for more LLM providers such as OpenAI, Claude, or local LLMs
- Add vector memory using pgvector, ChromaDB, or FAISS
- Add authentication using JWT
- Add workflow dashboard frontend
- Add human-in-the-loop approval
- Add Kubernetes deployment
- Add LangSmith tracing