import asyncio
import json
import asyncpg
from app.config import settings

pool = None


async def init_db(retries: int = 10, delay: int = 2):
    """
    Initialize PostgreSQL connection pool and create required tables.
    Retry logic is added because Docker may start the API before Postgres is ready.
    """
    global pool

    for attempt in range(retries):
        try:
            pool = await asyncpg.create_pool(settings.DATABASE_URL)

            async with pool.acquire() as conn:
                # Prevent API and worker from creating tables at the same time
                await conn.execute("SELECT pg_advisory_lock(12345);")
                try:
                    await conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflows (
                        id SERIAL PRIMARY KEY,
                        goal TEXT NOT NULL,
                        status TEXT NOT NULL,
                        result JSONB,
                        error TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                    """)

                    await conn.execute("""
                    CREATE TABLE IF NOT EXISTS agent_logs (
                        id SERIAL PRIMARY KEY,
                        workflow_id INT REFERENCES workflows(id),
                        agent_name TEXT NOT NULL,
                        input JSONB,
                        output JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                    """)

                    await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_workflows_result_jsonb
                    ON workflows USING GIN (result);
                    """)
                finally:
                    await conn.execute("SELECT pg_advisory_unlock(12345);")

            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"Database connection failed. Attempt {attempt + 1}/{retries}. Error: {e}")
            await asyncio.sleep(delay)

    raise RuntimeError("Could not connect to PostgreSQL after multiple retries.")


async def close_db():
    global pool
    if pool:
        await pool.close()


async def create_workflow(goal: str) -> int:
    async with pool.acquire() as conn:
        workflow_id = await conn.fetchval(
            """
            INSERT INTO workflows(goal, status)
            VALUES($1, 'PENDING')
            RETURNING id
            """,
            goal,
        )
        return workflow_id


async def get_workflow(workflow_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT id, goal, status, result, error, created_at, updated_at
            FROM workflows
            WHERE id=$1
            """,
            workflow_id,
        )


async def update_workflow_status(workflow_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workflows
            SET status=$1, updated_at=NOW()
            WHERE id=$2
            """,
            status,
            workflow_id,
        )


async def save_workflow_result(workflow_id: int, status: str, result: dict):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workflows
            SET status=$1, result=$2::jsonb, updated_at=NOW()
            WHERE id=$3
            """,
            status,
            json.dumps(result),
            workflow_id,
        )


async def save_workflow_error(workflow_id: int, error: str):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workflows
            SET status='FAILED', error=$1, updated_at=NOW()
            WHERE id=$2
            """,
            error,
            workflow_id,
        )


async def log_agent_step(
    workflow_id: int,
    agent_name: str,
    input_data: dict,
    output_data: dict,
):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO agent_logs(workflow_id, agent_name, input, output)
            VALUES($1, $2, $3::jsonb, $4::jsonb)
            """,
            workflow_id,
            agent_name,
            json.dumps(input_data),
            json.dumps(output_data),
        )