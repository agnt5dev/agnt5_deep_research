"""
AGNT5 Python SDK Benchmark Service

This package provides comprehensive benchmark components for testing AGNT5 platform functionality:
- Functions: Simple and LM-powered functions
- Session state: the chat tutor's conversation (entities.py)
- Workflows: Multi-step orchestration
- Agents: AI-powered agents with tools
- Tools: Reusable tool definitions
"""

# Import functions
from agnt5_benchmark.functions import (
    # Simple functions
    greet_user,
    add_numbers,
    create_user,
    long_task,
    flaky_function,
    failing_function,
    # LM-powered functions
    answer_bot,
    write_poem,
    analyze_sentiment,
    generate_story,
    chat_with_context,
    SentimentAnalysis,
)

# Import workflows
from agnt5_benchmark.workflows import (
    data_pipeline,
    order_fulfillment,
    long_workflow,
    tool_orchestrated_workflow,
    agent_research_workflow,
    agent_multi_step_workflow,
    simple_agentic_workflow,
    weather_report_workflow,
    chat_tutor_workflow,
    simple_chat_workflow,
    approval_workflow_hitl,
    agent_approval_workflow,
    agent_research_hitl,
    wf_36_approval_workflow_hitl,
    wf_37_multi_choice_workflow,
    wf_38_text_input_workflow,
    wf_39_agent_with_ask_user_tool,
    wf_40_agent_with_approval_tool,
    wf_41_multi_turn_conversation,
    # New workflows from agent-workflows task
    wf_42_sequential_context,
    wf_43_parallel_context,
    wf_44_parallel_tool_execution,
    wf_45_timing_comparison,
    wf_46_supervisor_worker,
    wf_47_debate_agents,
    wf_48_consensus_agents,
    wf_49_pipeline_agents,
)

# Import tools
from agnt5_benchmark.tools import (
    calculate_total,
    search_database,
    format_report,
    validate_data,
)

# Import agents
from agnt5_benchmark.agents import (
    tutor_agent,
    analyst_agent,
    researcher_agent,
    report_agent,
    history_tutor_agent,
    math_tutor_agent,
)

__all__ = [
    # Simple functions
    "greet_user",
    "add_numbers",
    "create_user",
    "long_task",
    "flaky_function",
    "failing_function",
    # LM-powered functions
    "answer_bot",
    "write_poem",
    "analyze_sentiment",
    "generate_story",
    "chat_with_context",
    "SentimentAnalysis",
    # Workflows
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
    # Tools
    "calculate_total",
    "search_database",
    "format_report",
    "validate_data",
    # Agents
    "tutor_agent",
    "analyst_agent",
    "researcher_agent",
    "report_agent",
    "history_tutor_agent",
    "math_tutor_agent",
]

__version__ = "1.0.0"
