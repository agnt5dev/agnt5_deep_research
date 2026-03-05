import asyncio
import os
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel
from agnt5 import Context, function, lm


# ============================================================================
# Simple Functions (No LM Dependencies)
# ============================================================================

@function
async def greet_user(ctx: Context, name: str) -> str:
    """Simple greeting function."""
    ctx.logger.info(f"Greeting user: {name}")
    return f"Hello, {name}!"


@function
async def add_numbers(ctx: Context, a: int, b: int) -> int:
    """Add two numbers."""
    ctx.logger.info(f"Adding numbers: {a} + {b}")
    return a + b


@function
async def create_user(ctx: Context, name: str, age: int, email: str) -> dict:
    """Create a User object."""
    ctx.logger.info(f"Creating user: {name}, {age}, {email}")

    user = {"name": name, "age": age, "email": email}
    return user


@function
async def long_task(ctx: Context, duration: int) -> dict:
    """Simulates a long-running task for benchmarking."""
    ctx.logger.info(f"Starting long task ({duration}s)")
    await asyncio.sleep(duration)
    return {"status": "completed", "duration": duration}


@function(retries={"max_attempts": 5, "initial_interval_ms": 100})
async def flaky_function(ctx: Context, fail_count: int) -> dict:
    """
    Fails `fail_count` times, then succeeds.

    Used to test retry logic and benchmark retry overhead.
    """
    attempt = ctx.attempt if hasattr(ctx, 'attempt') else 0

    ctx.logger.info(f"Flaky function attempt {attempt + 1}")

    if attempt < fail_count:
        raise Exception(f"Simulated failure (attempt {attempt + 1})")

    return {"succeeded": True, "attempts": attempt + 1}


@function
async def failing_function(ctx: Context, error: str) -> dict:
    """Always fails with given error message - for testing error handling."""
    ctx.logger.error(f"Failing with: {error}")
    raise Exception(error)


# ============================================================================
# LM-Powered Functions (Require OPENAI_API_KEY)
# ============================================================================

@function
async def answer_bot(ctx: Context, question: str) -> str:
    """Generate a response to a user's question."""
    ctx.logger.info(f"Answering question: {question}")

    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.error("OPENAI_API_KEY not set, cannot generate answer")
        raise ValueError("OPENAI_API_KEY not set")

    # Simple one-liner generation
    response = await lm.generate(
        model="openai/gpt-4o-mini",
        prompt="Answer the following question: " + question,
        temperature=0.7,
        max_tokens=1000
    )

    ctx.logger.info(f"Response: {response.text}\n")
    if response.usage:
        ctx.logger.info(f"Token usage: {response.usage.total_tokens} tokens")
        ctx.logger.info(f"  Prompt: {response.usage.prompt_tokens}")
        ctx.logger.info(f"  Completion: {response.usage.completion_tokens}\n")

    return response.text.strip()


@function
async def write_poem(ctx: Context, theme: str) -> str:
    """Generate a short poem on a given theme."""
    ctx.logger.info(f"Writing poem on theme: {theme}")

    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.error("OPENAI_API_KEY not set, cannot generate poem")
        raise ValueError("OPENAI_API_KEY not set")

    # Simple one-liner generation
    response = await lm.generate(
        model="openai/gpt-4o-mini",
        prompt="Write a short poem about " + theme,
        temperature=0.7,
        max_tokens=100
    )

    ctx.logger.info(f"Response: {response.text}\n")
    if response.usage:
        ctx.logger.info(f"Token usage: {response.usage.total_tokens} tokens")
        ctx.logger.info(f"  Prompt: {response.usage.prompt_tokens}")
        ctx.logger.info(f"  Completion: {response.usage.completion_tokens}\n")

    return response.text.strip()


@dataclass
class SentimentAnalysis:
    """Sentiment analysis result structure."""
    sentiment: str
    score: float
    keywords: List[str]


@function
async def analyze_sentiment(ctx: Context, text: str) -> dict:
    """Analyze sentiment using structured output.

    Tests LM structured output with dataclasses for benchmarking.
    Requires OPENAI_API_KEY.
    """
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.error("OPENAI_API_KEY not set, cannot analyze sentiment")
        raise ValueError("OPENAI_API_KEY not set")

    response = await lm.generate(
        model="openai/gpt-4o",
        prompt=f"Analyze the sentiment of this text: {text}",
        response_format=SentimentAnalysis,
        max_tokens=100
    )

    ctx.logger.info(f"LM analyzed sentiment: {response.structured_output}")
    return response.structured_output


@function
async def generate_story(ctx: Context, topic: str) -> dict:
    """Generate a short story using streaming for benchmarking.

    Tests LM streaming performance.
    Requires OPENAI_API_KEY.
    """
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.error("OPENAI_API_KEY not set, cannot generate story")
        raise ValueError("OPENAI_API_KEY not set")

    chunks = []
    async for chunk in lm.stream(
        model="openai/gpt-4o-mini",
        prompt=f"Write a very short story (2-3 sentences) about: {topic}",
        max_tokens=100
    ):
        chunks.append(chunk)

    story = "".join(chunks)
    ctx.logger.info(f"LM generated story with {len(chunks)} chunks")
    return {"story": story, "chunks": len(chunks)}


@function
async def chat_with_context(ctx: Context, user_message: str, context: list) -> dict:
    """Chat with conversation context for benchmarking multi-turn conversations.

    Tests multi-turn conversations with LM.
    Requires OPENAI_API_KEY.
    """
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.error("OPENAI_API_KEY not set, cannot chat")
        raise ValueError("OPENAI_API_KEY not set")

    # Build messages from context
    messages = context + [{"role": "user", "content": user_message}]

    response = await lm.generate(
        model="openai/gpt-4o-mini",
        messages=messages,
        max_tokens=100
    )

    ctx.logger.info(f"LM chat response generated")
    return {"response": response.text}


__all__ = [
    "greet_user",
    "add_numbers",
    "create_user",
    "long_task",
    "flaky_function",
    "failing_function",
    "answer_bot",
    "write_poem",
    "analyze_sentiment",
    "generate_story",
    "chat_with_context",
    "SentimentAnalysis",
]
