import json
import redis.asyncio as redis
from redis.exceptions import TimeoutError as RedisTimeoutError
from app.config import settings


redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=10,
    health_check_interval=30,
)


async def push_workflow_event(workflow_id: int):
    """
    Push a workflow ID into Redis Stream.
    The worker will consume this event later.
    """
    await redis_client.xadd(
        settings.WORKFLOW_STREAM,
        {"workflow_id": str(workflow_id)},
    )


async def read_workflow_events(last_id: str = "0-0"):
    """
    Read workflow events from Redis Stream.
    If no event arrives, return an empty list instead of crashing.
    """
    try:
        events = await redis_client.xread(
            {settings.WORKFLOW_STREAM: last_id},
            block=5000,
            count=1,
        )
        return events

    except RedisTimeoutError:
        return []


async def save_short_term_memory(workflow_id: int, state: dict):
    """
    Save temporary workflow memory in Redis.
    """
    key = f"workflow:{workflow_id}:memory"

    await redis_client.hset(
        key,
        mapping={
            "state": json.dumps(state)
        }
    )


async def get_short_term_memory(workflow_id: int):
    """
    Read temporary workflow memory from Redis.
    """
    key = f"workflow:{workflow_id}:memory"
    memory = await redis_client.hgetall(key)

    if not memory:
        return {}

    if "state" in memory:
        memory["state"] = json.loads(memory["state"])

    return memory