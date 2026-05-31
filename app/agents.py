from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.tools import research_tool, summarize_tool, validation_tool
from app.db import log_agent_step
from app.redis_client import save_short_term_memory


class WorkflowState(TypedDict):
    workflow_id: int
    goal: str
    plan: List[str]
    outputs: List[Dict[str, Any]]
    final_answer: str
    validation_passed: bool
    retry_count: int
    error: str


MAX_RETRIES = 2


async def planner_agent(state: WorkflowState) -> WorkflowState:
    """
    Planner Agent:
    Breaks the user goal into a structured plan.
    """
    goal = state["goal"]

    plan = [
        f"Understand the user goal: {goal}",
        f"Collect useful information about: {goal}",
        "Generate a clear final summary",
        "Validate the final summary for quality",
        "Store the final workflow memory",
    ]

    state["plan"] = plan

    await log_agent_step(
        workflow_id=state["workflow_id"],
        agent_name="planner_agent",
        input_data={"goal": goal},
        output_data={"plan": plan},
    )

    return state


async def executor_agent(state: WorkflowState) -> WorkflowState:
    """
    Executor Agent:
    Uses tools to perform the actual task.
    """
    goal = state["goal"]

    research_result = await research_tool(goal)
    summary = await summarize_tool(research_result)

    output = {
        "research_result": research_result,
        "summary": summary,
        "attempt": state["retry_count"] + 1,
    }

    state["outputs"].append(output)
    state["final_answer"] = summary

    await log_agent_step(
        workflow_id=state["workflow_id"],
        agent_name="executor_agent",
        input_data={
            "goal": goal,
            "plan": state["plan"],
            "attempt": state["retry_count"] + 1,
        },
        output_data=output,
    )

    return state


async def validator_agent(state: WorkflowState) -> WorkflowState:
    """
    Validator Agent:
    Checks whether the executor output is acceptable.
    """
    validation_result = await validation_tool(state["final_answer"])

    state["validation_passed"] = validation_result["valid"]

    if validation_result["valid"]:
        state["error"] = ""
    else:
        state["retry_count"] += 1
        state["error"] = validation_result["reason"]

    await log_agent_step(
        workflow_id=state["workflow_id"],
        agent_name="validator_agent",
        input_data={"final_answer": state["final_answer"]},
        output_data=validation_result,
    )

    return state


async def memory_agent(state: WorkflowState) -> WorkflowState:
    """
    Memory Agent:
    Saves short-term workflow state in Redis.
    """
    memory_data = {
        "goal": state["goal"],
        "plan": state["plan"],
        "outputs": state["outputs"],
        "final_answer": state["final_answer"],
        "validation_passed": state["validation_passed"],
        "retry_count": state["retry_count"],
    }

    await save_short_term_memory(
        workflow_id=state["workflow_id"],
        state=memory_data,
    )

    await log_agent_step(
        workflow_id=state["workflow_id"],
        agent_name="memory_agent",
        input_data={"workflow_id": state["workflow_id"]},
        output_data={"memory_saved": True},
    )

    return state


def validation_router(state: WorkflowState):
    """
    Dynamic router:
    Decides the next agent based on validation result.
    """
    if state["validation_passed"]:
        return "memory_agent"

    if state["retry_count"] <= MAX_RETRIES:
        return "executor_agent"

    return END


def build_workflow_graph():
    """
    Builds the LangGraph workflow.
    """
    graph = StateGraph(WorkflowState)

    graph.add_node("planner_agent", planner_agent)
    graph.add_node("executor_agent", executor_agent)
    graph.add_node("validator_agent", validator_agent)
    graph.add_node("memory_agent", memory_agent)

    graph.set_entry_point("planner_agent")

    graph.add_edge("planner_agent", "executor_agent")
    graph.add_edge("executor_agent", "validator_agent")

    graph.add_conditional_edges(
        "validator_agent",
        validation_router,
        {
            "executor_agent": "executor_agent",
            "memory_agent": "memory_agent",
            END: END,
        },
    )

    graph.add_edge("memory_agent", END)

    return graph.compile()


async def run_agentic_workflow(workflow_id: int, goal: str) -> dict:
    """
    Runs the full multi-agent workflow.
    """
    workflow_app = build_workflow_graph()

    initial_state: WorkflowState = {
        "workflow_id": workflow_id,
        "goal": goal,
        "plan": [],
        "outputs": [],
        "final_answer": "",
        "validation_passed": False,
        "retry_count": 0,
        "error": "",
    }

    final_state = await workflow_app.ainvoke(initial_state)

    return {
        "goal": final_state["goal"],
        "plan": final_state["plan"],
        "outputs": final_state["outputs"],
        "final_answer": final_state["final_answer"],
        "validation_passed": final_state["validation_passed"],
        "retry_count": final_state["retry_count"],
        "error": final_state["error"],
    }