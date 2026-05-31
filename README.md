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