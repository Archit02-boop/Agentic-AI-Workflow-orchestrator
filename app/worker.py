import asyncio

from app.db import (
    init_db,
    get_workflow,
    update_workflow_status,
    save_workflow_result,
    save_workflow_error,
)
from app.redis_client import read_workflow_events
from app.agents import run_agentic_workflow


async def process_workflow(workflow_id: int):
    workflow = await get_workflow(workflow_id)

    if not workflow:
        print(f"Workflow {workflow_id} not found.")
        return

    goal = workflow["goal"]

    try:
        await update_workflow_status(workflow_id, "RUNNING")

        result = await run_agentic_workflow(
            workflow_id=workflow_id,
            goal=goal,
        )

        if result["validation_passed"]:
            await save_workflow_result(
                workflow_id=workflow_id,
                status="COMPLETED",
                result=result,
            )
        else:
            await save_workflow_result(
                workflow_id=workflow_id,
                status="FAILED",
                result=result,
            )

        print(f"Workflow {workflow_id} processed successfully.")

    except Exception as e:
        await save_workflow_error(workflow_id, str(e))
        print(f"Workflow {workflow_id} failed. Error: {e}")


async def worker_loop():
    await init_db()

    last_id = "0-0"

    print("Worker started. Waiting for workflow events...")

    while True:
        events = await read_workflow_events(last_id)

        if not events:
            continue

        for stream_name, messages in events:
            for message_id, data in messages:
                last_id = message_id

                workflow_id = int(data["workflow_id"])

                print(f"Received workflow event: {workflow_id}")

                await process_workflow(workflow_id)


if __name__ == "__main__":
    asyncio.run(worker_loop())