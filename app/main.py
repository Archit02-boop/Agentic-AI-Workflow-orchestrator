import json
from fastapi import FastAPI, HTTPException

from app.models import WorkflowCreateRequest, WorkflowResponse
from app.db import (
    init_db,
    close_db,
    create_workflow,
    get_workflow,
)
from app.redis_client import push_workflow_event


app = FastAPI(
    title="Agentic AI Workflow Orchestrator",
    description="A multi-agent workflow orchestration backend using FastAPI, Redis, PostgreSQL, LangGraph, and Gemini LLM.",
    version="2.0.0",
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


@app.get("/")
async def root():
    return {
        "message": "Agentic AI Workflow Orchestrator is running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok"
    }


@app.post("/workflows", response_model=WorkflowResponse)
async def create_new_workflow(request: WorkflowCreateRequest):
    workflow_id = await create_workflow(request.goal)

    await push_workflow_event(workflow_id)

    return WorkflowResponse(
        workflow_id=workflow_id,
        status="PENDING",
        result=None,
    )


@app.get("/workflows/{workflow_id}")
async def read_workflow(workflow_id: int):
    workflow = await get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )

    result = workflow["result"]

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = {
                "raw_result": result
            }

    return {
        "workflow_id": workflow["id"],
        "goal": workflow["goal"],
        "status": workflow["status"],
        "result": result,
        "error": workflow["error"],
        "created_at": str(workflow["created_at"]),
        "updated_at": str(workflow["updated_at"]),
    }