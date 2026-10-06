#!/usr/bin/env python3
"""SDK Python Benchmark - AGNT5 Worker."""

import asyncio
import os
import sys
import logging
from agnt5 import Worker


# Import components for explicit registration (hybrid approach)
from agnt5_benchmark import (
    # Workflows
    data_pipeline,
                order_fulfillment,
                long_workflow,
                tool_orchestrated_workflow,
                agent_research_workflow,
                agent_multi_step_workflow,
                simple_agentic_workflow,
                weather_report_workflow,
                simple_chat_workflow,
                chat_tutor_workflow,
                approval_workflow_hitl,
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
    # Agents
    tutor_agent,
    analyst_agent,
    researcher_agent,
    history_tutor_agent,
    math_tutor_agent,
    report_agent,
    # Optional: standalone functions (can be invoked directly via API)
    greet_user,
    add_numbers,
    answer_bot
)

from agnt5_benchmark.workflows import simple_agentic_workflow, weather_report_workflow, simple_chat_workflow, chat_tutor_workflow, approval_workflow_hitl

# Configure logging (this will also control Rust log levels via PyO3-log)
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG to see all Rust logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SERVICE_NAME = "sdk-python-benchmark"

async def main():
    """Main entry point for the worker."""
    logger.info("Starting %s worker...", SERVICE_NAME)

    # Configuration from environment
    coordinator_endpoint = os.getenv("AGNT5_COORDINATOR_ENDPOINT", "http://localhost:34186")
    tenant_id = os.getenv("AGNT5_TENANT_ID")
    deployment_id = os.getenv("AGNT5_DEPLOYMENT_ID")

    # Log the IDs we're seeing
    logger.info(f"Environment variables - TENANT_ID: {tenant_id}, DEPLOYMENT_ID: {deployment_id}")

    # Note: The SDK should read these from environment variables automatically
    # AGNT5_TENANT_ID and AGNT5_DEPLOYMENT_ID must be set in the environment

    try:
        worker = Worker(
            service_name=SERVICE_NAME,
            service_version="1.0.0",
            coordinator_endpoint=coordinator_endpoint,
            runtime="standalone",
            # Hybrid registration: workflows/agents explicit, tools auto-included
            workflows=[
                data_pipeline,
                order_fulfillment,
                long_workflow,
                tool_orchestrated_workflow,
                agent_research_workflow,
                agent_multi_step_workflow,
                simple_agentic_workflow,
                weather_report_workflow,
                simple_chat_workflow,
                chat_tutor_workflow,
                approval_workflow_hitl,
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
            ],
            agents=[tutor_agent, analyst_agent, researcher_agent, report_agent, history_tutor_agent, math_tutor_agent],
            functions=[greet_user, add_numbers, answer_bot]  # Optional standalone functions,
        )

        # Components are explicitly registered, tools are auto-included from agents
        logger.info("Worker created successfully with explicit component registration")

        # Start the worker (this is async and will block until shutdown)
        logger.info("Starting worker and registering with coordinator...")
        await worker.run()

    except ImportError as e:
        logger.error("Make sure to install agnt5: pip install agnt5")
        return 1
    except Exception as e:
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
