import asyncio
from google import genai
from app.config import settings


def get_gemini_client():
    """
    Creates a Gemini client using the API key from environment variables.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing. Please set it in your .env file.")

    return genai.Client(api_key=settings.GEMINI_API_KEY)


async def call_gemini(prompt: str) -> str:
    """
    Async wrapper around Gemini text generation.

    The Google GenAI SDK call is synchronous, so asyncio.to_thread()
    prevents it from blocking the event loop.
    """
    client = get_gemini_client()

    def generate():
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        return response.text

    return await asyncio.to_thread(generate)


def fallback_research(query: str) -> str:
    """
    Fallback research output if Gemini fails.
    """
    return (
        f"Fallback Research for '{query}': "
        "This topic includes background context, market trends, opportunities, "
        "challenges, and practical use cases. The fallback response is generated "
        "locally so the workflow can continue even when the LLM API is unavailable."
    )


def fallback_summary(text: str) -> str:
    """
    Fallback summary output if Gemini fails.
    """
    return f"""
Final Summary:

- Overview:
{text}

- Key Trends:
The market is evolving with increasing adoption, automation, digital platforms, and data-driven decision making.

- Opportunities:
There are opportunities in product innovation, operational efficiency, user experience improvement, and scalable platform development.

- Challenges:
Key challenges include cost, reliability, infrastructure, competition, regulation, and integration complexity.

- Practical Use Cases:
This can be applied in business analysis, automation workflows, research summarization, decision support, and intelligent assistant systems.

- Conclusion:
The topic shows strong potential, but successful implementation requires reliable architecture, validation, monitoring, and scalable execution.
"""


async def research_tool(query: str) -> str:
    """
    LLM-powered research-style tool with fallback.
    """
    prompt = f"""
You are a research assistant.

Task:
Create a concise but useful research note on the following topic:

{query}

Include:
1. Background
2. Current trends
3. Opportunities
4. Challenges
5. Practical use cases

Keep it clear and interview/project-demo friendly.
"""

    try:
        return await call_gemini(prompt)

    except Exception as e:
        print(f"Gemini research_tool failed. Using fallback. Error: {e}")
        return fallback_research(query)


async def summarize_tool(text: str) -> str:
    """
    LLM-powered summarization tool with fallback.
    """
    prompt = f"""
You are an expert summarizer.

Summarize the following research into a final structured answer.

Research:
{text}

Output format:
Final Summary:
- Overview:
- Key Trends:
- Opportunities:
- Challenges:
- Practical Use Cases:
- Conclusion:
"""

    try:
        return await call_gemini(prompt)

    except Exception as e:
        print(f"Gemini summarize_tool failed. Using fallback. Error: {e}")
        return fallback_summary(text)


async def validation_tool(output: str) -> dict:
    """
    Rule-based validation tool.

    Validation remains deterministic so the workflow stays predictable.
    """
    await asyncio.sleep(0.1)

    if not output or len(output.strip()) < 100:
        return {
            "valid": False,
            "reason": "Output is too short or empty."
        }

    required_sections = [
        "Final Summary",
        "Overview",
        "Key Trends",
        "Opportunities",
        "Challenges",
        "Practical Use Cases",
        "Conclusion",
    ]

    missing_sections = [
        section for section in required_sections
        if section.lower() not in output.lower()
    ]

    if missing_sections:
        return {
            "valid": False,
            "reason": f"Missing required sections: {', '.join(missing_sections)}"
        }

    return {
        "valid": True,
        "reason": "Output passed validation checks."
    }