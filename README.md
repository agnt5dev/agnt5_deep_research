# sdk-python-benchmark

AI-focused benchmark blueprint showcasing the latest AGNT5 Python SDK features with real LLM integration, streaming, multi-provider support, and advanced AI workflows.

## Overview

This blueprint demonstrates production-ready AI patterns using the AGNT5 platform:

- **Real LLM Integration**: OpenAI, Anthropic, Groq, and other providers
- **Streaming Responses**: Real-time token streaming for better UX
- **Multi-Provider Support**: Provider comparison and fallback strategies
- **Session state**: Conversations that carry over between runs sharing a session
- **Agents**: LLM-backed agents with tool orchestration
- **Workflows**: Complex AI workflows using ctx.task(), ctx.parallel(), and ctx.gather()

## Features

### Functions

**LLM Generation** (`functions/llm_generate.py`):
- `llm_simple_generate`: Basic LLM generation with any provider
- `llm_conversation`: Multi-turn conversations with message history
- `llm_with_system_prompt`: Role-based generation with system prompts
- `llm_code_generation`: Code generation with language-specific prompting
- `llm_summarize`: Text summarization with style options
- `llm_translate`: Language translation

**LLM Streaming** (`functions/llm_stream.py`):
- `llm_stream_generate`: Basic streaming with statistics
- `llm_stream_conversation`: Streaming multi-turn conversations
- `llm_stream_with_callback`: Streaming with chunk processing callbacks
- `llm_stream_creative_writing`: Creative content generation
- `llm_stream_code_explanation`: Code explanation with streaming

**Multi-Provider** (`functions/multi_provider_llm.py`):
- `compare_providers`: Compare responses from multiple providers
- `provider_fallback`: Automatic fallback to alternative providers
- `provider_cost_comparison`: Cost analysis across providers
- `provider_quality_comparison`: Quality-based provider selection

**Classic AI Functions**:
- `generate_llm_response`: Simulated LLM generation (no API needed)
- `embed_and_search`: Vector embeddings and semantic search
- `extract_entities`: NLP entity extraction and sentiment analysis
- `chain_prompts`: Multi-step reasoning chains
- `evaluate_response`: AI response quality evaluation

### Workflows

All workflows use modern SDK patterns (`ctx.task()`, `ctx.parallel()`, `ctx.gather()`):

- `simple_ai_generation`: Basic generate → evaluate pattern
- `streaming_generation`: Streaming LLM responses
- `multi_provider_workflow`: Parallel provider comparison
- `rag_pipeline`: Retrieval-Augmented Generation
- `content_analysis`: Parallel entity extraction + summarization
- `multi_step_reasoning`: Chain-of-thought with parallel evaluation
- `conversation_workflow`: Multi-turn conversation handling
- `code_generation_workflow`: Code generation + explanation
- `creative_writing_workflow`: Creative content with streaming
- `provider_fallback_workflow`: Resilient provider fallback
- `translation_workflow`: Translation with back-translation validation

### Session state

`chat_tutor_workflow` keeps its conversation in session-scoped state
(`ctx.session.state`, wrapped by `TutorConversation` in `entities.py`). Runs
that share a `session_id` continue the same conversation, and the history
survives worker restarts.

### Agents

Real LLM-backed agents with tool orchestration:

- `researcher`: Research agent with database and statistics tools
- `assistant`: General-purpose conversational agent
- `code_expert`: Programming specialist
- `creative_writer`: Creative content generation
- `data_analyst`: Data analysis and insights
- `customer_support`: Customer service agent
- `multi_tool_agent`: Comprehensive tool access

### Tools

- `search_database`: Database search simulation
- `calculate_statistics`: Statistical calculations
- `format_data`: Data formatting (JSON, YAML, CSV)
- `web_search`: Web search simulation
- `get_weather`: Weather information

## Setup

### Prerequisites

Set environment variables for the LLM providers you want to use:

```bash
# OpenAI (recommended for most examples)
export OPENAI_API_KEY=your-openai-key

# Anthropic (optional)
export ANTHROPIC_API_KEY=your-anthropic-key

# Groq (optional - fast inference)
export GROQ_API_KEY=your-groq-key

# OpenRouter (optional - access to many models)
export OPENROUTER_API_KEY=your-openrouter-key
```

### Installation

```bash
# Install dependencies
uv pip install --editable .[dev]

# Run tests
pytest

# Run benchmarks
pytest tests/test_benchmarks.py --benchmark-only
```

## Usage

### Start the Worker

```bash
# Start worker (connects to AGNT5 platform)
python app.py
```

Or use the development script with hot reload:

```bash
./scripts/run-dev.sh
```

### Testing with HTTP

See `examples.http` for comprehensive HTTP request examples, including:

- LLM generation (sync and streaming)
- Multi-provider comparisons
- Conversation workflows
- Agent queries
- Workflow executions

### Example: Simple LLM Generation

```bash
curl -X POST http://localhost:8080/call \
  -H "Content-Type: application/json" \
  -d '{
    "serviceName": "sdk-python-benchmark",
    "handlerName": "llm_simple_generate",
    "inputData": {
      "prompt": "Explain machine learning in one sentence",
      "model": "openai/gpt-4o-mini"
    }
  }'
```

### Example: Streaming Response

```bash
curl -X POST http://localhost:8080/call \
  -H "Content-Type: application/json" \
  -d '{
    "serviceName": "sdk-python-benchmark",
    "handlerName": "llm_stream_generate",
    "inputData": {
      "prompt": "Write a haiku about AI",
      "model": "openai/gpt-4o-mini"
    }
  }'
```

### Example: Multi-Provider Comparison

```bash
curl -X POST http://localhost:8080/call \
  -H "Content-Type: application/json" \
  -d '{
    "serviceName": "sdk-python-benchmark",
    "handlerName": "compare_providers",
    "inputData": {
      "prompt": "What is the meaning of life?",
      "providers": [
        "openai/gpt-4o-mini",
        "anthropic/claude-3-5-haiku-20241022",
        "groq/llama-3.3-70b-versatile"
      ]
    }
  }'
```

## AI Patterns Demonstrated

### 1. Real LLM Integration

Use actual LLM providers with the `lm` module:

```python
from agnt5 import lm

# Simple generation
response = await lm.generate(
    model="openai/gpt-4o-mini",
    prompt="Hello, world!",
    temperature=0.7,
    max_tokens=100
)

# Streaming
async for chunk in lm.stream(
    model="openai/gpt-4o-mini",
    prompt="Tell me a story"
):
    print(chunk, end="", flush=True)
```

### 2. Session State for Conversations

State scoped to a session persists across the runs that share its `session_id`:

```python
from agnt5 import WorkflowContext, workflow

@workflow(chat=True)
async def chat(ctx: WorkflowContext, message: str) -> str:
    history = await ctx.session.state.get("messages", [])
    history.append({"role": "user", "content": message})
    reply = f"You said: {message}"
    history.append({"role": "assistant", "content": reply})
    await ctx.session.state.set("messages", history)
    return reply
```

### 3. Modern Workflow Patterns

Use `ctx.task()`, `ctx.parallel()`, and `ctx.gather()`:

```python
@workflow
async def parallel_workflow(ctx: Context, query: str):
    # Run tasks in parallel
    result1, result2 = await ctx.parallel(
        ctx.task("service", "func1", input=query),
        ctx.task("service", "func2", input=query)
    )

    # Named parallel execution
    results = await ctx.gather(
        summary=ctx.task("service", "summarize", input=result1),
        analysis=ctx.task("service", "analyze", input=result2)
    )

    return results
```

### 4. Multi-Provider Fallback

Resilient LLM calls with provider fallback:

```python
@function
async def resilient_generate(ctx: Context, prompt: str):
    fallback_chain = [
        "openai/gpt-4o-mini",
        "groq/llama-3.3-70b-versatile",
        "anthropic/claude-3-5-haiku-20241022"
    ]

    for provider in fallback_chain:
        try:
            return await lm.generate(model=provider, prompt=prompt)
        except Exception as e:
            ctx.logger.warning(f"Failed with {provider}: {e}")
            continue

    raise Exception("All providers failed")
```

## Development

### Project Structure

```
sdk-python-benchmark/
├── src/agnt5_benchmark/
│   ├── __init__.py
│   ├── agents.py             # Agent definitions
│   ├── entities.py           # Chat tutor session state
│   ├── tools.py              # Tool definitions
│   ├── workflows.py          # Workflow definitions
│   └── functions/            # Function definitions
│       ├── __init__.py
│       ├── chain_prompts.py
│       ├── embed_and_search.py
│       ├── evaluate_response.py
│       ├── extract_entities.py
│       ├── generate_llm_response.py  # Simulated (no API)
│       ├── llm_generate.py           # Real LLM (sync)
│       ├── llm_stream.py             # Real LLM (streaming)
│       └── multi_provider_llm.py     # Multi-provider patterns
├── tests/
│   ├── conftest.py
│   ├── test_benchmarks.py
│   └── test_functions.py
├── app.py                    # Worker entry point
├── examples.http             # HTTP request examples
├── pyproject.toml
└── README.md
```

### Adding New Functions

1. Create function in `src/agnt5_benchmark/functions/`
2. Import in `functions/__init__.py`
3. Add tests in `tests/test_functions.py`
4. Add examples in `examples.http`

### Adding New Workflows

1. Add workflow to `src/agnt5_benchmark/workflows.py`
2. Use `ctx.task()`, `ctx.parallel()`, or `ctx.gather()`
3. Add tests and examples

## Testing

```bash
# Run all tests
pytest

# Run benchmarks only
pytest tests/test_benchmarks.py --benchmark-only

# Run with coverage
pytest --cov=agnt5_benchmark

# Run specific test
pytest tests/test_functions.py::test_llm_generate
```

## Performance Considerations

- **Simulated functions** (e.g., `generate_llm_response`) are fast and free - good for testing
- **Real LLM functions** (e.g., `llm_simple_generate`) require API keys and have latency
- **Streaming** provides better perceived latency for long responses
- **Provider fallback** adds resilience but increases latency on failures
- **Parallel execution** (`ctx.parallel()`) reduces total workflow time

## Cost Optimization

1. **Use simulated functions** for development and testing
2. **Choose cheaper providers** (e.g., OpenAI GPT-4o-mini, Groq) for non-critical tasks
3. **Set max_tokens** appropriately to avoid excessive costs
4. **Use provider comparison** to understand cost/quality tradeoffs
5. **Implement caching** for repeated queries

## Supported Providers

- **OpenAI**: `openai/gpt-4o-mini`, `openai/gpt-4o`, etc.
- **Anthropic**: `anthropic/claude-3-5-haiku-20241022`, `anthropic/claude-3-5-sonnet-20241022`, etc.
- **Groq**: `groq/llama-3.3-70b-versatile`, etc.
- **OpenRouter**: `openrouter/anthropic/claude-3.5-haiku`, etc.

See the [AGNT5 SDK documentation](https://docs.agnt5.com) for the complete list of supported providers.

## Resources

- [AGNT5 Documentation](https://docs.agnt5.com)
- [AGNT5 GitHub](https://github.com/agnt5/agnt5)
- [SDK Examples](../../sdk/sdk-python/examples/)
- [Issue Tracker](https://github.com/agnt5/agnt5/issues)

## License

MIT License - See LICENSE file for details
