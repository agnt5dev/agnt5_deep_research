"""
Benchmark Workflows for Testing Multi-Step Orchestration

Provides multi-step workflows for testing durability and state management.
"""

import asyncio
import os
from typing import Dict, List

from agnt5 import Agent, Context, function, workflow, WorkflowContext
from agnt5.tool import AskUserTool, RequestApprovalTool
from agnt5_benchmark.agents import analyst_agent, report_agent, researcher_agent, anthropic_weather_agent
from agnt5_benchmark.entities import TutorConversation
from agnt5_benchmark.tools import calculate_total, format_report, search_database, validate_data, get_weather


# ============================================================================
# Helper Functions for Workflows
# ============================================================================

@function
async def fetch_data(ctx: Context, source: str) -> Dict:
    """Simulate fetching data from a source."""
    ctx.logger.info(f"Fetching data from {source}...")
    await asyncio.sleep(0.1)  # Simulate I/O
    return {"source": source, "data": [1, 2, 3, 4, 5]}


@function
async def process_data(ctx: Context, data: Dict) -> Dict:
    """Process fetched data."""
    ctx.logger.info(f"Processing data from {data['source']}...")
    await asyncio.sleep(0.1)  # Simulate processing
    total = sum(data["data"])
    return {"source": data["source"], "total": total, "count": len(data["data"])}


# ============================================================================
# Benchmark Workflows
# ============================================================================

@workflow
async def data_pipeline(ctx: Context, source: str) -> Dict:
    """Simple sequential data processing pipeline.

    Phase 1: Each step runs sequentially using local function calls.
    Phase 2: Will support distributed execution and durable checkpoints.
    """
    ctx.logger.info(f"Starting data pipeline for {source}")

    # Step 1: Fetch data
    data = await ctx.task("data-service", "fetch_data", input=source)

    # Step 2: Process data
    result = await ctx.task("data-service", "process_data", input=data)

    ctx.logger.info(f"Pipeline completed: {result}")
    return result


@workflow
async def order_fulfillment(ctx: Context, order_id: str, items: list = None) -> dict:
    """
    Multi-step order processing workflow for benchmarking.

    Tests:
    - Multi-step workflow execution
    - State persistence across steps
    - Error handling in workflows
    """
    if items is None:
        items = []

    ctx.logger.info(f"Starting order fulfillment for order {order_id}")

    # Step 1: Validate order
    ctx.logger.info("Step 1: Validating order")
    await asyncio.sleep(0.1)  # Simulate validation

    # Step 2: Process payment
    ctx.logger.info("Step 2: Processing payment")
    await asyncio.sleep(0.1)  # Simulate payment processing
    payment_id = f"pay_{order_id}"

    # Step 3: Reserve inventory
    ctx.logger.info("Step 3: Reserving inventory")
    await asyncio.sleep(0.1)  # Simulate inventory check

    # Step 4: Ship order
    ctx.logger.info("Step 4: Shipping order")
    await asyncio.sleep(0.1)  # Simulate shipping
    tracking_number = f"TRACK_{order_id}"

    return {
        "order_id": order_id,
        "status": "completed",
        "payment_id": payment_id,
        "tracking_number": tracking_number,
        "items_count": len(items),
        "steps_completed": 4
    }


@workflow
async def long_workflow(ctx: Context, steps: int) -> dict:
    """
    Multi-step workflow for testing crash recovery and benchmarking.

    Tests:
    - Workflow state survives worker crashes
    - Workflow can resume from last completed step
    - Long-running workflow durability
    """
    ctx.logger.info(f"Starting long workflow with {steps} steps")

    results = []
    for i in range(steps):
        ctx.logger.info(f"Executing step {i + 1}/{steps}")
        await asyncio.sleep(0.05)  # Simulate step processing
        results.append(f"step_{i + 1}_completed")

    return {
        "status": "completed",
        "total_steps": steps,
        "steps_completed": steps,
        "results": results
    }


@workflow
async def tool_orchestrated_workflow(ctx: Context, numbers: list[float], query: str) -> dict:
    """
    Workflow that directly invokes tools for processing.

    Tests:
    - Direct tool invocation in workflows
    - Tool result handling
    - Multiple tool coordination
    """
    ctx.logger.info(f"Starting tool orchestrated workflow")

    # Step 1: Validate input data
    ctx.logger.info("Step 1: Validating input data")
    validation_result = await validate_data(ctx, data={"numbers": numbers, "query": query}, required_fields=["numbers", "query"])

    if not validation_result["is_valid"]:
        return {
            "status": "failed",
            "error": validation_result["message"],
        }

    # Step 2: Calculate statistics
    ctx.logger.info("Step 2: Calculating statistics")
    sum_result = await calculate_total(ctx, numbers=numbers, operation="sum")
    avg_result = await calculate_total(ctx, numbers=numbers, operation="average")

    # Step 3: Search database
    ctx.logger.info("Step 3: Searching database")
    search_results = await search_database(ctx, query=query, limit=3)

    # Step 4: Format report
    ctx.logger.info("Step 4: Formatting report")
    report_data = {
        "total_sum": sum_result["result"],
        "average": avg_result["result"],
        "count": len(numbers),
        "search_results_count": len(search_results),
    }
    report = await format_report(ctx, data=report_data, format_style="summary")

    return {
        "status": "completed",
        "validation": validation_result,
        "statistics": {
            "sum": sum_result["result"],
            "average": avg_result["result"],
            "count": len(numbers),
        },
        "search_results": search_results,
        "report": report,
    }


@workflow(chat=True)
async def agent_research_workflow(ctx: Context, research_topic: str) -> dict:
    """
    Workflow using an agent with tools to perform research.

    Tests:
    - Agent integration in workflows
    - Agent tool orchestration
    - LLM-driven tool selection
    """
    ctx.logger.info(f"Starting agent research workflow for: {research_topic}")

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.warning("OPENAI_API_KEY not set, skipping agent execution")
        return {
            "status": "skipped",
            "reason": "OPENAI_API_KEY not configured",
            "research_topic": research_topic,
        }

    # Step 1: Create research agent with tools
    ctx.logger.info("Step 1: Creating research agent")
    research_agent = Agent(
        name="researcher",
        model="openai/gpt-4o-mini",
        instructions="""You are a research assistant. You MUST use the search_database tool to find information.

        Required steps:
        1. ALWAYS call search_database tool first to find relevant information
        2. Use calculate_total if you need statistics
        3. Use format_report to format your findings

        Do not answer from your own knowledge - you must use the tools provided.""",
        tools=[search_database, calculate_total, format_report],
        temperature=0.7,
        max_iterations=5,
    )

    # Step 2: Execute research task
    ctx.logger.info("Step 2: Agent executing research")
    result = await research_agent.run(
        f"Research the topic: {research_topic}. Search for information and provide a summary.",
        context=ctx,
    )

    # Step 3: Process results
    ctx.logger.info("Step 3: Processing research results")

    return {
        "status": "completed",
        "research_topic": research_topic,
        "agent_output": result.output,
        "tool_calls_made": len(result.tool_calls),
        "tools_used": [tc["name"] for tc in result.tool_calls],
    }


@workflow(chat=True)
async def agent_multi_step_workflow(ctx: Context, task: str, data_points: list[float]) -> dict:
    """
    Complex workflow with agent using multiple tools across steps.

    Tests:
    - Multi-step agent workflows
    - Agent state across workflow steps
    - Complex tool orchestration
    """
    ctx.logger.info(f"Starting multi-step agent workflow: {task}")

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.warning("OPENAI_API_KEY not set, skipping agent execution")
        return {
            "status": "skipped",
            "reason": "OPENAI_API_KEY not configured",
            "task": task,
        }

    # Step 1: Data analysis phase
    ctx.logger.info("Step 1: Data analysis phase")
    analysis_result = await analyst_agent.run(
        f"Analyze these data points: {data_points}. Calculate sum, average, and provide insights.",
        context=ctx,
    )

    # Step 2: Research phase
    ctx.logger.info("Step 2: Research phase")
    # Extract keywords from task for search
    search_query = task.split()[0] if task else "analytics"
    research_result = await researcher_agent.run(
        f"Search for information about: {search_query}",
        context=ctx,
    )

    # Step 3: Report generation phase
    ctx.logger.info("Step 3: Report generation phase")
    final_result = await report_agent.run(
        f"Create a report about '{task}' combining:\n"
        f"Analysis: {analysis_result.output}\n"
        f"Research: {research_result.output}",
        context=ctx,
    )

    return {
        "status": "completed",
        "task": task,
        "data_points_count": len(data_points),
        "analysis_output": analysis_result.output,
        "research_output": research_result.output,
        "final_report": final_result.output,
        "total_tool_calls": (
            len(analysis_result.tool_calls) + len(research_result.tool_calls) + len(final_result.tool_calls)
        ),
    }

@workflow(chat=True)
async def simple_agentic_workflow(ctx:WorkflowContext, message: str) -> str:
    """
    Simple workflow demonstrating agent interaction.

    Tests:
    - Basic agent invocation in workflow
    """
    ctx.logger.info(f"Starting simple agentic workflow with message: {message}")

    # Create a simple agent
    simple_agent = Agent(
        name="simple-agent",
        model="openai/gpt-4o-mini",
        instructions="You are a helpful assistant. Respond to the user's message clearly and concisely.",
        temperature=0.5,
    )

    # Run the agent with the provided message
    result = await simple_agent.run(
        f"User message: {message}\nPlease respond appropriately.",
        context=ctx,
    )

    return result.output


@workflow(chat=True)
async def weather_report_workflow(ctx: WorkflowContext, location: str) -> dict:
    """
    Workflow that uses an agent to get weather information.

    Tests:
    - Agent tool usage within a workflow
    """
    ctx.logger.info(f"Starting weather report workflow for location: {location}")

    # Create an agent with the get_weather tool
    weather_agent = Agent(
        name="weather-agent",
        model="openai/gpt-4o-mini",
        instructions="""You are a weather assistant. You MUST use the get_weather tool to provide accurate weather information.

        Required steps:
        1. ALWAYS call get_weather tool with the location provided
        2. Provide a clear and concise weather report based on the tool's output.""",
        tools=[get_weather],
        temperature=0.5,
    )

    # Run the agent to get the weather report
    result = await weather_agent.run(
        f"Provide the current weather for the location: {location}.",
        context=ctx,
    )

    return {
        "status": "completed",
        "location": location,
        "weather_report": result.output,
        "tool_calls_made": len(result.tool_calls),
    }


@workflow(chat=True)
async def chat_tutor_workflow(ctx: WorkflowContext, message: str, session_id: str = None) -> dict:
    """
    Simple chat-based tutor workflow that keeps its conversation in session state.

    This workflow demonstrates:
    - Chat interface without using agents
    - Session-based conversation tracking with ctx.session.state
    - State management across multiple workflow executions
    - Persistence - the conversation survives worker restarts
    - Simple response generation

    Args:
        message: User's message
        session_id: Session identifier (auto-generated by platform if not provided)

    Architecture:
    - TutorConversation keeps the conversation in session-scoped state
    - That state persists across workflow executions in the same session
    - Each session_id has its own conversation
    - TutorConversation's methods handle all state changes (add_message, set_topic, etc.)
    """
    ctx.logger.info(f"Tutor workflow - session_id: {session_id}, message: {message}")

    # The conversation lives in session state, so it carries over between runs
    # that share this session_id.
    conversation = TutorConversation(ctx)

    # Add user message to conversation history (auto-persists)
    await conversation.add_message("user", message)

    # Get current conversation state
    messages = await conversation.get_messages()
    topic = await conversation.get_topic()
    message_count = await conversation.get_message_count()

    # Detect topic from first user message if still on default
    if topic == "general" and message_count == 1:
        # Simple topic detection
        if any(word in message.lower() for word in ["python", "programming", "code"]):
            detected_topic = "programming"
        elif any(word in message.lower() for word in ["math", "calculate", "number"]):
            detected_topic = "mathematics"
        else:
            detected_topic = "general"
        await conversation.set_topic(detected_topic)
        topic = detected_topic

    # Generate contextual response based on conversation history
    user_message_count = len([m for m in messages if m["role"] == "user"])
    if user_message_count == 1:
        response = f"Hello! I see you're interested in {topic}. {message} - Let me help you with that!"
    else:
        # Show awareness of conversation history
        response = f"Continuing our discussion on {topic}. You asked: '{message}'. Based on our {user_message_count} messages, here's my response..."

    # Add assistant response to conversation history (auto-persists)
    await conversation.add_message("assistant", response)

    ctx.logger.info(f"Updated conversation: {message_count} messages, topic: {topic}")

    # Get updated state for response
    all_messages = await conversation.get_messages()

    return {
        "output": response,
        "session_id": session_id,
        "message_count": message_count,
        "topic": topic,
        "conversation_history": all_messages[-5:]  # Last 5 messages for debugging
    }


@workflow(chat=True)
async def simple_chat_workflow(ctx: WorkflowContext, message: str, session_id: str = None) -> str:
    """
    Minimal chat workflow example without agents or complex state.

    This workflow demonstrates:
    - Simplest possible chat workflow
    - Direct message echoing with context
    - Session tracking via session_id parameter

    Args:
        message: User's message
        session_id: Session identifier (auto-generated by platform if not provided)

    Returns:
        Response string
    """
    ctx.logger.info(f"Simple chat - session: {session_id}, message: {message}")

    # Simple response generation based on message content
    if "hello" in message.lower() or "hi" in message.lower():
        response = f"Hello! You said: '{message}'. How can I help you today?"
    elif "bye" in message.lower():
        response = f"Goodbye! Thanks for chatting. (Session: {session_id[:8]}...)"
    elif "?" in message:
        response = f"You asked: '{message}'. That's a great question! Let me think about it..."
    else:
        response = f"I received your message: '{message}'. This is a simple chat workflow example."

    # Note: session_id is automatically handled by the platform
    # - Extracted from input by SDK
    # - Returned in response metadata
    # - Frontend persists it for next message

    return response


@workflow(chat=True)
async def approval_workflow_hitl(ctx: WorkflowContext, message: str, session_id: str = None) -> dict:
    """
    Human-in-the-loop workflow with approval step.

    Tests:
    - Workflow pauses for user input
    - User approval/rejection flow
    - Workflow resumes after user response
    - State persistence during pause
    """
    ctx.logger.info(f"Starting approval workflow with message: {message}")

    # Step 1: Process the message
    ctx.logger.info("Step 1: Processing message")
    processed = message.upper()
    await asyncio.sleep(0.1)  # Simulate processing

    # Step 2: Ask for user approval (PAUSES HERE)
    ctx.logger.info("Step 2: Requesting user approval")
    decision = await ctx.wait_for_user(
        f"Approve processing result: '{processed}'?",
        input_type="approval",
        options=[
            {"id": "yes", "label": "Approve"},
            {"id": "no", "label": "Reject"}
        ]
    )

    # Step 3: Handle decision
    ctx.logger.info(f"Step 3: User decision received: {decision}")
    if decision == "yes":
        # Continue with approval path
        await asyncio.sleep(0.1)
        return {
            "status": "approved",
            "message": message,
            "processed": processed,
            "decision": decision
        }
    else:
        # Rejection path
        return {
            "status": "rejected",
            "message": message,
            "processed": processed,
            "decision": decision
        }


@workflow(chat=True)
async def agent_approval_workflow(ctx: WorkflowContext, task: str, session_id: str = None) -> dict:
    """
    Workflow demonstrating agent using RequestApprovalTool for human-in-the-loop approvals.

    This workflow shows how an agent can pause execution to request user approval
    during its reasoning process. The agent analyzes the task and then uses the
    RequestApprovalTool to ask for permission before proceeding.

    Tests:
    - Agent integration with RequestApprovalTool
    - Workflow pause/resume with agent tool calls
    - Human-in-the-loop approval pattern
    """
    ctx.logger.info(f"Starting agent approval workflow with task: {task}")

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.warning("OPENAI_API_KEY not set, skipping agent execution")
        return {
            "status": "skipped",
            "reason": "OPENAI_API_KEY not configured",
            "task": task,
        }

    # Create agent with approval tool
    approval_agent = Agent(
        name="approval_agent",
        model="openai/gpt-4o-mini",
        instructions="""You are a deployment assistant that helps users deploy code changes safely.

        Your workflow:
        1. Analyze the deployment task
        2. Identify potential risks
        3. Use the request_approval tool to ask for user approval before proceeding
        4. If approved, confirm the deployment plan
        5. If rejected, explain what alternative approaches exist

        Always use the request_approval tool before making important decisions.""",
        tools=[RequestApprovalTool(ctx)],
        temperature=0.5,
    )

    # Run agent - it will pause when it calls request_approval
    result = await approval_agent.run(
        f"Analyze and prepare for deployment: {task}",
        context=ctx,
    )

    return {
        "status": "completed",
        "task": task,
        "agent_output": result.output,
        "tool_calls_made": len(result.tool_calls),
        "tools_used": [tc["name"] for tc in result.tool_calls],
    }


@workflow(chat=True)
async def agent_research_hitl(ctx: WorkflowContext, topic: str, session_id: str = None) -> dict:
    """
    Workflow demonstrating agent using AskUserTool for clarifying questions.

    This workflow shows how an agent can pause execution to ask the user for
    additional information during research. The agent uses AskUserTool to gather
    more specific requirements mid-execution.

    Tests:
    - Agent integration with AskUserTool
    - Text input collection via agent tool
    - Multi-turn agent interaction with human input
    """
    ctx.logger.info(f"Starting agent research workflow with topic: {topic}")

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        ctx.logger.warning("OPENAI_API_KEY not set, skipping agent execution")
        return {
            "status": "skipped",
            "reason": "OPENAI_API_KEY not configured",
            "topic": topic,
        }

    # Create agent with ask_user tool
    research_agent = Agent(
        name="research_agent",
        model="openai/gpt-4o-mini",
        instructions="""You are a research assistant that helps users explore topics in depth.

        Your workflow:
        1. Understand the research topic
        2. If the topic is broad, use ask_user tool to ask what specific aspect they want to focus on
        3. Conduct focused research based on their input
        4. Provide detailed findings

        Use the ask_user tool when you need clarification or want to narrow the scope.""",
        tools=[AskUserTool(ctx), search_database],
        temperature=0.7,
        max_iterations=5,
    )

    # Run agent - it will pause when it calls ask_user
    result = await research_agent.run(
        f"Research the topic: {topic}. Ask me for clarification if needed.",
        context=ctx,
    )

    return {
        "status": "completed",
        "topic": topic,
        "agent_output": result.output,
        "tool_calls_made": len(result.tool_calls),
        "tools_used": [tc["name"] for tc in result.tool_calls],
    }

@workflow
async def wf_36_approval_workflow_hitl(ctx: WorkflowContext, message: str) -> dict:
    """Test Scenario: Workflow that pauses for approval.

    Demonstrates human-in-the-loop approval pattern where a workflow
    processes input, pauses for user decision, then continues based
    on the approval/rejection.

    Args:
        message: Message to process that requires approval

    Returns:
        Result dictionary with approval status and processing result

    MCP Verification Points:
        - Logs: Initial processing, pause request, approval decision
        - Events: workflow.paused (with approval options)
        - Entity State: Message and approval status in workflow state
    """
    ctx.logger.info("=== HITL: Approval Workflow ===")
    ctx.logger.info(f"Processing message: {message}")

    # Step 1: Store initial data in state
    ctx.state.set("original_message", message)
    ctx.state.set("status", "pending_approval")
    ctx.logger.info("State: Message stored, awaiting approval")

    # Step 2: Analyze the message (pre-approval processing)
    word_count = len(message.split())
    char_count = len(message)
    ctx.state.set("word_count", word_count)
    ctx.state.set("char_count", char_count)
    ctx.logger.info(f"Analysis: {word_count} words, {char_count} characters")

    # Step 3: Pause for user approval
    ctx.logger.info("⏸️  Requesting user approval...")
    decision = await ctx.wait_for_user(
        question=f"Approve processing of message: '{message}'? (Words: {word_count}, Chars: {char_count})",
        input_type="approval",
        options=[
            {"id": "approve", "label": "Approve"},
            {"id": "reject", "label": "Reject"},
        ],
    )

    # Step 4: Process based on decision
    ctx.logger.info(f"▶️  User decision received: {decision}")
    ctx.state.set("approval_decision", decision)

    if decision == "approve":
        ctx.state.set("status", "approved")
        ctx.logger.info("✅ Message approved - processing")

        # Perform approved processing
        processed_message = message.upper()
        ctx.state.set("processed_message", processed_message)

        return {
            "status": "approved",
            "message": message,
            "processed": processed_message,
            "word_count": word_count,
            "char_count": char_count,
        }
    else:
        ctx.state.set("status", "rejected")
        ctx.logger.info("❌ Message rejected - no processing")

        return {
            "status": "rejected",
            "message": message,
            "processed": False,
            "reason": "User rejected approval",
        }


@workflow
async def wf_37_multi_choice_workflow(ctx: WorkflowContext, task: str) -> dict:
    """Test Scenario: Workflow with multi-choice user input.

    Demonstrates human-in-the-loop multi-choice pattern where a workflow
    presents multiple options to the user and processes based on selection.

    Args:
        task: Task description requiring choice selection

    Returns:
        Result dictionary with selected choice and processing result

    MCP Verification Points:
        - Logs: Task presentation, choice options, selection processing
        - Events: workflow.paused (with choice options)
        - Entity State: Task and choice selection in workflow state
    """
    ctx.logger.info("=== HITL: Multi-Choice Workflow ===")
    ctx.logger.info(f"Task: {task}")

    # Step 1: Store task in state
    ctx.state.set("task", task)
    ctx.state.set("status", "awaiting_choice")

    # Step 2: Present processing options to user
    ctx.logger.info("⏸️  Presenting processing options to user...")
    choice = await ctx.wait_for_user(
        question=f"How should we process task '{task}'?",
        input_type="choice",
        options=[
            {"id": "fast", "label": "Fast Processing (lower quality)"},
            {"id": "balanced", "label": "Balanced Processing (medium quality)"},
            {"id": "thorough", "label": "Thorough Processing (highest quality)"},
        ],
    )

    # Step 3: Process based on choice
    ctx.logger.info(f"▶️  User selected: {choice}")
    ctx.state.set("processing_mode", choice)
    ctx.state.set("status", "processing")

    # Simulate different processing based on choice
    processing_results = {
        "fast": {
            "duration": "1 second",
            "quality": "70%",
            "details": "Quick analysis completed",
        },
        "balanced": {
            "duration": "5 seconds",
            "quality": "85%",
            "details": "Standard analysis completed",
        },
        "thorough": {
            "duration": "15 seconds",
            "quality": "95%",
            "details": "Deep analysis completed with comprehensive review",
        },
    }

    result = processing_results.get(
        choice,
        {"duration": "unknown", "quality": "unknown", "details": "Invalid choice"},
    )

    ctx.logger.info(f"✅ Processing complete: {result['details']}")
    ctx.state.set("status", "completed")
    ctx.state.set("result", result)

    return {
        "task": task,
        "choice": choice,
        "duration": result["duration"],
        "quality": result["quality"],
        "details": result["details"],
    }


@workflow
async def wf_38_text_input_workflow(ctx: WorkflowContext, prompt: str = "Enter text") -> dict:
    """Test Scenario: Workflow that pauses for text input.

    Demonstrates human-in-the-loop free-text input pattern where a workflow
    collects arbitrary text from the user and incorporates it into processing.

    Args:
        prompt: Prompt message to display to user

    Returns:
        Result dictionary with user input and processing result

    MCP Verification Points:
        - Logs: Prompt display, text input reception, processing
        - Events: workflow.paused (with text input prompt)
        - Entity State: Prompt and user input in workflow state
    """
    ctx.logger.info("=== HITL: Text Input Workflow ===")
    ctx.logger.info(f"Prompt: {prompt}")

    # Step 1: Store prompt in state
    ctx.state.set("prompt", prompt)
    ctx.state.set("status", "awaiting_input")

    # Step 2: Request text input from user
    ctx.logger.info(f"⏸️  Requesting user input: {prompt}")
    user_input = await ctx.wait_for_user(
        question=prompt,
        input_type="text",
    )

    # Step 3: Process the user's text input
    ctx.logger.info(f"▶️  User input received: {user_input}")
    ctx.state.set("user_input", user_input)
    ctx.state.set("status", "processing")

    # Analyze the input
    input_length = len(user_input)
    word_count = len(user_input.split())
    has_numbers = any(char.isdigit() for char in user_input)
    has_special = any(not char.isalnum() and not char.isspace() for char in user_input)

    analysis = {
        "length": input_length,
        "word_count": word_count,
        "has_numbers": has_numbers,
        "has_special_chars": has_special,
    }

    ctx.logger.info(f"✅ Input analysis: {analysis}")
    ctx.state.set("analysis", analysis)
    ctx.state.set("status", "completed")

    # Create a processed response
    response = f"Received '{user_input}' ({word_count} words, {input_length} chars)"

    return {
        "prompt": prompt,
        "user_input": user_input,
        "response": response,
        "analysis": analysis,
    }


@workflow
async def wf_39_agent_with_ask_user_tool(
    ctx: WorkflowContext, task: str = "Help me plan a birthday party"
) -> dict:
    """Test Scenario: Agent that uses AskUserTool to gather information.

    Demonstrates agent-based HITL where the agent autonomously decides when
    to ask the user for clarifying information. The agent can ask multiple
    questions in sequence to gather all necessary details.

    Args:
        task: Initial task description from user

    Returns:
        Result dictionary with final output and interaction details

    MCP Verification Points:
        - Logs: Agent reasoning, tool invocations, user questions/responses
        - Events: Multiple workflow.paused/resumed events for each question
        - Entity State: Agent conversation history preserved across pauses
        - Traces: Agent span containing multiple ask_user tool call spans
    """
    ctx.logger.info("=== HITL: Agent with AskUserTool ===")
    ctx.logger.info(f"Initial task: {task}")

    # Store initial task in state
    ctx.state.set("task", task)
    ctx.state.set("status", "agent_starting")

    # Initialize agent with AskUserTool
    # The agent will autonomously decide when to ask questions
    planner_agent = Agent(
        name="PlannerAgent",
        model="openai/gpt-4o-mini",
        instructions=(
            "You are a helpful planning assistant. When you need more information "
            "from the user to complete their task, use the ask_user tool to ask "
            "clarifying questions. Ask one question at a time. Gather all necessary "
            "details before providing your final plan. Keep responses concise."
        ),
        tools=[AskUserTool(ctx)],  # Agent can ask questions
        temperature=0.7,
        max_iterations=15,  # Allow multiple rounds of Q&A
    )

    # Run agent - it will autonomously decide when to ask questions
    ctx.logger.info("🤖 Starting agent execution...")
    ctx.state.set("status", "agent_running")

    result = await planner_agent.run(task, context=ctx)

    ctx.logger.info(f"✅ Agent completed with output: {result.output[:100]}...")

    # Extract tool calls to analyze interaction
    ask_user_calls = [tc for tc in result.tool_calls if tc.get("name") == "ask_user"]

    ctx.logger.info(f"📊 Agent asked {len(ask_user_calls)} questions")
    ctx.state.set("questions_asked", len(ask_user_calls))
    ctx.state.set("status", "completed")

    return {
        "task": task,
        "output": result.output,
        "questions_asked": len(ask_user_calls),
        "tool_calls": result.tool_calls,
        "agent_iterations": len(result.tool_calls) + 1,
    }


@workflow
async def wf_40_agent_with_approval_tool(
    ctx: WorkflowContext, action_request: str = "Deploy the new feature to production"
) -> dict:
    """Test Scenario: Agent that requests approval before executing actions.

    Demonstrates agent-based approval workflow where the agent analyzes
    a requested action, explains the implications, and requests user
    approval before proceeding.

    Args:
        action_request: The action being requested

    Returns:
        Result dictionary with approval status and agent output

    MCP Verification Points:
        - Logs: Agent reasoning, approval requests, user decisions
        - Events: workflow.paused/resumed for approval request
        - Entity State: Action details and approval status in state
        - Traces: Agent span with request_approval tool call span
    """
    ctx.logger.info("=== HITL: Agent with RequestApprovalTool ===")
    ctx.logger.info(f"Action request: {action_request}")

    # Store request in state
    ctx.state.set("action_request", action_request)
    ctx.state.set("status", "analyzing_request")

    # Initialize agent with RequestApprovalTool
    deployment_agent = Agent(
        name="DeploymentAgent",
        model="openai/gpt-4o-mini",
        instructions=(
            "You are a deployment safety assistant. When a user requests an action, "
            "analyze it carefully and identify any risks or requirements. Then use the "
            "request_approval tool to get user confirmation before proceeding. "
            "Explain what will happen if approved. Keep responses concise."
        ),
        tools=[RequestApprovalTool(ctx)],  # Agent can request approval
        temperature=0.7,
        max_iterations=10,
    )

    # Run agent - it will analyze and request approval
    ctx.logger.info("🤖 Starting agent analysis...")
    ctx.state.set("status", "agent_running")

    result = await deployment_agent.run(action_request, context=ctx)

    ctx.logger.info(f"✅ Agent completed with output: {result.output[:100]}...")

    # Extract approval tool calls
    approval_calls = [tc for tc in result.tool_calls if tc.get("name") == "request_approval"]

    approval_status = "approved" if approval_calls else "not_required"
    if approval_calls:
        # Check the result of the approval call
        last_approval = approval_calls[-1]
        if "result" in last_approval:
            approval_status = last_approval["result"]

    ctx.logger.info(f"📊 Approval status: {approval_status}")
    ctx.state.set("approval_status", approval_status)
    ctx.state.set("status", "completed")

    return {
        "action_request": action_request,
        "output": result.output,
        "approval_status": approval_status,
        "approval_calls": len(approval_calls),
        "tool_calls": result.tool_calls,
    }


@workflow(chat=True)
async def wf_41_multi_turn_conversation(
    ctx: WorkflowContext, session_id: str, message: str
) -> dict:
    """Test Scenario: Multi-turn conversation with session-based history.

    Demonstrates chat=True functionality where agents automatically persist
    conversation history across multiple workflow invocations using AgentContext
    with session_id. Each turn adds to the conversation, allowing the agent
    to remember previous context.

    Args:
        session_id: Unique session identifier to group conversation turns
        message: New user message for this turn

    Returns:
        Result dictionary with response, turn count, and session metadata

    MCP Verification Points:
        - Logs: Agent reasoning, message tracking, turn progression
        - Entity: AgentSession entity persists conversation automatically
        - Traces: Each turn creates workflow span with agent span
        - Events: Entity state updates for agent conversation history
    """
    ctx.logger.info("=== HITL: Multi-Turn Conversation (chat=True) ===")
    ctx.logger.info(f"Session ID: {session_id}")
    ctx.logger.info(f"New message: {message}")

    # Create AgentContext with session_id for conversation persistence
    # This automatically handles loading/saving conversation history
    from agnt5 import AgentContext

    agent_ctx = AgentContext(
        run_id=ctx.run_id,
        agent_name="ChatAssistant",
        session_id=session_id,  # Key for multi-turn persistence
        parent_context=ctx,  # Inherit workflow context
    )

    # Get metadata before processing (shows conversation state)
    metadata_before = await agent_ctx.get_metadata()
    message_count_before = metadata_before.get("message_count", 0)
    ctx.logger.info(f"📚 Session has {message_count_before} messages before this turn")

    # Create agent
    chat_agent = Agent(
        name="ChatAssistant",
        model="openai/gpt-4o-mini",
        instructions=(
            "You are a helpful chat assistant. You can see the full conversation "
            "history and should reference previous messages when relevant. "
            "Keep responses concise and natural."
        ),
        temperature=0.7,
        max_iterations=5,
    )

    ctx.logger.info(f"🤖 Running agent (turn {message_count_before // 2 + 1})...")

    # Run agent - it automatically loads history, adds user message, and saves
    result = await chat_agent.run(message, context=agent_ctx)

    assistant_response = result.output
    ctx.logger.info(f"💬 Agent response: {assistant_response[:100]}...")

    # Get metadata after processing
    metadata_after = await agent_ctx.get_metadata()
    message_count_after = metadata_after.get("message_count", 0)
    turn_count = message_count_after // 2  # Each turn = 1 user + 1 assistant message

    ctx.logger.info(f"✅ Turn {turn_count} complete ({message_count_after} total messages)")

    return {
        "session_id": session_id,
        "role": "assistant",  # Indicate this is an assistant response
        "response": assistant_response,
        "turn_count": turn_count,
        "total_messages": message_count_after,
        "metadata": metadata_after,
    }


# =============================================================================
# CONTEXT PROPAGATION WORKFLOWS (from ex_13)
# =============================================================================


@workflow
async def wf_42_sequential_context(ctx: WorkflowContext, input_data: str) -> dict:
    """
    Sequential context propagation through workflow steps.

    Each step receives context from previous steps and adds to it.
    Demonstrates context accumulation as workflow progresses.
    """
    ctx.logger.info(f"Starting sequential context workflow with: {input_data}")

    # Step 1: Parse input
    ctx.state.set("original_input", input_data)
    parsed = await ctx.step("parse", lambda: {
        "words": input_data.split(),
        "length": len(input_data),
        "uppercase": input_data.upper(),
    })
    ctx.state.set("parsed", parsed)

    # Step 2: Analyze (uses result from step 1)
    analysis = await ctx.step("analyze", lambda: {
        "word_count": len(parsed["words"]),
        "char_count": parsed["length"],
        "has_uppercase": any(c.isupper() for c in input_data),
    })
    ctx.state.set("analysis", analysis)

    # Step 3: Enrich (uses results from steps 1 and 2)
    enriched = await ctx.step("enrich", lambda: {
        "summary": f"{analysis['word_count']} words, {analysis['char_count']} chars",
        "transformed": parsed["uppercase"],
    })

    return {
        "input": input_data,
        "parsed": parsed,
        "analysis": analysis,
        "enriched": enriched,
        "pattern": "sequential_context",
    }


@workflow
async def wf_43_parallel_context(ctx: WorkflowContext, text: str) -> dict:
    """
    Parallel context propagation with multiple analysis branches.

    Multiple analysis tasks run in parallel, results are merged.
    """
    ctx.logger.info(f"Starting parallel context workflow")

    ctx.state.set("input_text", text)

    async def analyze_length():
        await asyncio.sleep(0.05)
        return {"char_count": len(text), "word_count": len(text.split())}

    async def analyze_content():
        await asyncio.sleep(0.05)
        words = text.lower().split()
        return {"unique_words": len(set(words)), "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0}

    async def analyze_structure():
        await asyncio.sleep(0.05)
        return {"sentences": text.count(".") + text.count("!") + text.count("?"), "has_punctuation": any(c in text for c in ".,!?;:")}

    # Execute all in parallel
    length_result, content_result, structure_result = await asyncio.gather(
        ctx.step("analyze_length", analyze_length()),
        ctx.step("analyze_content", analyze_content()),
        ctx.step("analyze_structure", analyze_structure()),
    )

    merged = {
        "length": length_result,
        "content": content_result,
        "structure": structure_result,
        "parallel_branches": 3,
    }

    return {
        "input": text,
        "parallel_results": merged,
        "pattern": "parallel_context",
    }


# =============================================================================
# PARALLEL TOOL CALL WORKFLOWS (from ex_14)
# =============================================================================


@workflow
async def wf_44_parallel_tool_execution(ctx: WorkflowContext, sources: List[str]) -> dict:
    """
    Multiple independent tools run concurrently.

    Demonstrates parallelization for improved performance.
    """
    import time
    ctx.logger.info(f"Starting parallel execution for {len(sources)} sources")
    start_time = time.time()

    # Execute fetches in parallel
    async def fetch_source(source: str):
        await asyncio.sleep(0.1)  # Simulate I/O
        return {"source": source, "data": [1, 2, 3, 4, 5]}

    fetch_tasks = [fetch_source(source) for source in sources]
    fetched_results = await asyncio.gather(*fetch_tasks)

    # Transform in parallel
    async def transform_data(data: list):
        await asyncio.sleep(0.05)
        return {"transformed": [x * 2 for x in data]}

    transform_tasks = [transform_data(result["data"]) for result in fetched_results]
    transformed_results = await asyncio.gather(*transform_tasks)

    elapsed = (time.time() - start_time) * 1000

    return {
        "sources": sources,
        "parallel_fetches": len(fetched_results),
        "parallel_transforms": len(transformed_results),
        "execution_time_ms": round(elapsed, 2),
        "pattern": "parallel_tool_execution",
    }


@workflow
async def wf_45_timing_comparison(ctx: WorkflowContext, num_operations: int = 5) -> dict:
    """
    Compare sequential vs parallel execution timing.

    Runs the same operations both ways to show performance difference.
    """
    import time
    ctx.logger.info(f"Timing comparison with {num_operations} operations")
    delay_per_op = 50  # ms

    async def slow_operation(name: str, delay_ms: int):
        await asyncio.sleep(delay_ms / 1000)
        return {"name": name, "completed": True}

    # Sequential
    seq_start = time.time()
    for i in range(num_operations):
        await slow_operation(f"seq_{i}", delay_per_op)
    seq_time = (time.time() - seq_start) * 1000

    # Parallel
    par_start = time.time()
    tasks = [slow_operation(f"par_{i}", delay_per_op) for i in range(num_operations)]
    await asyncio.gather(*tasks)
    par_time = (time.time() - par_start) * 1000

    speedup = seq_time / par_time if par_time > 0 else 0

    return {
        "num_operations": num_operations,
        "sequential_time_ms": round(seq_time, 2),
        "parallel_time_ms": round(par_time, 2),
        "speedup_factor": round(speedup, 2),
        "pattern": "timing_comparison",
    }


# =============================================================================
# MULTI-AGENT ORCHESTRATION WORKFLOWS (from ex_16)
# =============================================================================


@workflow(chat=True)
async def wf_46_supervisor_worker(ctx: WorkflowContext, task: str) -> dict:
    """
    Supervisor delegates subtasks to specialized workers.

    Demonstrates agents-as-tools pattern for task decomposition.
    """
    ctx.logger.info(f"Starting supervisor/worker for: {task}")

    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "skipped", "reason": "OPENAI_API_KEY not configured", "task": task}

    # Workers
    research_worker = Agent(
        name="research_worker",
        model="openai/gpt-4o-mini",
        instructions="You are a research worker. Provide 3-5 bullet points of findings. Be concise.",
        temperature=0.5,
        max_iterations=3,
    )

    analysis_worker = Agent(
        name="analysis_worker",
        model="openai/gpt-4o-mini",
        instructions="You are an analyst. Provide 2-3 key insights. Be analytical and precise.",
        temperature=0.5,
        max_iterations=3,
    )

    # Supervisor
    supervisor = Agent(
        name="supervisor",
        model="openai/gpt-4o-mini",
        instructions="""You are a supervisor coordinating a team.
        Use research_worker to gather information.
        Use analysis_worker to analyze findings.
        Synthesize their work into a cohesive output.""",
        tools=[research_worker, analysis_worker],
        temperature=0.5,
        max_iterations=10,
    )

    result = await supervisor.run_sync(f"Complete this task: {task}")

    return {
        "task": task,
        "final_output": result.output,
        "tool_calls": len(result.tool_calls),
        "workers_used": [tc.get("name", "unknown") for tc in result.tool_calls],
        "pattern": "supervisor_worker",
    }


@workflow(chat=True)
async def wf_47_debate_agents(ctx: WorkflowContext, topic: str) -> dict:
    """
    Two agents argue different perspectives, third decides.

    Demonstrates debate pattern for multi-perspective analysis.
    """
    ctx.logger.info(f"Starting debate on: {topic}")

    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "skipped", "reason": "OPENAI_API_KEY not configured", "topic": topic}

    proponent = Agent(
        name="proponent",
        model="openai/gpt-4o-mini",
        instructions="You argue IN FAVOR of the topic. Present 3 strong arguments. Be concise.",
        temperature=0.7,
        max_iterations=3,
    )

    opponent = Agent(
        name="opponent",
        model="openai/gpt-4o-mini",
        instructions="You argue AGAINST the topic. Present 3 counterarguments. Be concise.",
        temperature=0.7,
        max_iterations=3,
    )

    judge = Agent(
        name="judge",
        model="openai/gpt-4o-mini",
        instructions="You are an impartial judge. Evaluate both sides. Make a reasoned decision: FOR or AGAINST.",
        temperature=0.3,
        max_iterations=3,
    )

    # Opening statements
    pro_result = await proponent.run_sync(f"Argue FOR: {topic}")
    con_result = await opponent.run_sync(f"Argue AGAINST: {topic}")

    # Judge's decision
    judgment = await judge.run_sync(
        f"Topic: {topic}\n\nFOR:\n{pro_result.output}\n\nAGAINST:\n{con_result.output}\n\nDecide."
    )

    return {
        "topic": topic,
        "pro_arguments": pro_result.output,
        "con_arguments": con_result.output,
        "judgment": judgment.output,
        "pattern": "debate",
    }


@workflow(chat=True)
async def wf_48_consensus_agents(ctx: WorkflowContext, question: str) -> dict:
    """
    Multiple agents vote to reach consensus on a decision.

    Each agent votes, consensus determined by majority.
    """
    ctx.logger.info(f"Starting consensus for: {question}")

    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "skipped", "reason": "OPENAI_API_KEY not configured", "question": question}

    agents = [
        Agent(name="pragmatist", model="openai/gpt-4o-mini",
              instructions="You are pragmatic. Consider feasibility. Vote YES or NO briefly.",
              temperature=0.5, max_iterations=3),
        Agent(name="innovator", model="openai/gpt-4o-mini",
              instructions="You favor innovation. Consider long-term benefits. Vote YES or NO briefly.",
              temperature=0.7, max_iterations=3),
        Agent(name="conservative", model="openai/gpt-4o-mini",
              instructions="You are risk-averse. Consider stability. Vote YES or NO briefly.",
              temperature=0.3, max_iterations=3),
    ]

    votes = []
    for agent in agents:
        result = await agent.run_sync(f"Question: {question}\nVote YES or NO with one sentence reasoning.")
        vote_text = result.output.upper()
        vote = "YES" if "YES" in vote_text else "NO" if "NO" in vote_text else "ABSTAIN"
        votes.append({"agent": agent.name, "vote": vote, "reasoning": result.output})

    yes_count = sum(1 for v in votes if v["vote"] == "YES")
    no_count = sum(1 for v in votes if v["vote"] == "NO")
    consensus = "YES" if yes_count > no_count else "NO" if no_count > yes_count else "TIE"

    return {
        "question": question,
        "votes": votes,
        "vote_summary": {"yes": yes_count, "no": no_count},
        "consensus_decision": consensus,
        "pattern": "consensus",
    }


@workflow(chat=True)
async def wf_49_pipeline_agents(ctx: WorkflowContext, content: str) -> dict:
    """
    Agents form a processing pipeline.

    Each agent transforms content and passes to the next.
    """
    ctx.logger.info(f"Starting pipeline for: {content[:50]}...")

    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "skipped", "reason": "OPENAI_API_KEY not configured", "content": content}

    extractor = Agent(name="extractor", model="openai/gpt-4o-mini",
                      instructions="Extract 3-5 key facts as bullet points.", temperature=0.3, max_iterations=3)

    enricher = Agent(name="enricher", model="openai/gpt-4o-mini",
                     instructions="Add context to each fact. Keep additions brief.", temperature=0.5, max_iterations=3)

    summarizer = Agent(name="summarizer", model="openai/gpt-4o-mini",
                       instructions="Create a coherent paragraph summary.", temperature=0.5, max_iterations=3)

    # Pipeline execution
    stage1 = await extractor.run_sync(f"Extract key facts:\n{content}")
    stage2 = await enricher.run_sync(f"Enrich:\n{stage1.output}")
    stage3 = await summarizer.run_sync(f"Summarize:\n{stage2.output}")

    return {
        "input": content,
        "stages": [
            {"stage": "extract", "output": stage1.output},
            {"stage": "enrich", "output": stage2.output},
            {"stage": "summarize", "output": stage3.output},
        ],
        "final_output": stage3.output,
        "pattern": "pipeline",
    }


@workflow
async def wf_50_anthropic_tool_calling(ctx: WorkflowContext, location: str = "San Francisco") -> Dict:
    """
    Test workflow for AGNT5-195: Anthropic tool calling fix.

    Tests that Anthropic models (claude-sonnet-4-5) correctly call tools
    when provided with clear instructions and all required parameters.

    Args:
        location: Location to get weather for (default: San Francisco)

    Returns:
        Dict with agent output, tool calls made, and test status
    """
    ctx.logger.info(f"Testing Anthropic tool calling for location: {location}")

    # Run the Anthropic agent with a clear instruction that requires tool use
    result = await anthropic_weather_agent.run_sync(f"What's the weather in {location}?")

    # Extract tool call information from metadata
    tool_calls_made = 0
    tools_used = []

    if hasattr(result, "metadata") and result.metadata:
        tool_calls_made = result.metadata.get("tool_calls_made", 0)
        tools_used = result.metadata.get("tools_used", [])

    # Test passes if tool was called at least once
    test_passed = tool_calls_made > 0 and "get_weather" in tools_used

    ctx.logger.info(f"Tool calls made: {tool_calls_made}, Tools used: {tools_used}")

    return {
        "location": location,
        "agent_output": result.output,
        "tool_calls_made": tool_calls_made,
        "tools_used": tools_used,
        "test_passed": test_passed,
        "bug_fix": "AGNT5-195",
        "status": "PASS" if test_passed else "FAIL",
    }


__all__ = [
    "data_pipeline",
    "order_fulfillment",
    "long_workflow",
    "tool_orchestrated_workflow",
    "agent_research_workflow",
    "agent_multi_step_workflow",
    "simple_agentic_workflow",
    "weather_report_workflow",
    "chat_tutor_workflow",
    "simple_chat_workflow",
    "approval_workflow_hitl",
    "agent_approval_workflow",
    "agent_research_hitl",
    "wf_36_approval_workflow_hitl",
    "wf_37_multi_choice_workflow",
    "wf_38_text_input_workflow",
    "wf_39_agent_with_ask_user_tool",
    "wf_40_agent_with_approval_tool",
    "wf_41_multi_turn_conversation",
    # New workflows from agent-workflows task
    "wf_42_sequential_context",
    "wf_43_parallel_context",
    "wf_44_parallel_tool_execution",
    "wf_45_timing_comparison",
    "wf_46_supervisor_worker",
    "wf_47_debate_agents",
    "wf_48_consensus_agents",
    "wf_49_pipeline_agents",
    "wf_50_anthropic_tool_calling",
]