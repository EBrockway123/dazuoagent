"""LLM agent for whole-house customization.

`agent.py` is the runtime (LangChain/LangGraph agent, tool dispatch).
`tools.py` exposes individual tools the agent can call.
`prompts.py` holds the system prompts.

When `settings.llm_provider == "mock"` (the default), `chat()` returns a
deterministic stub reply so the rest of the stack is exercisable without an
API key. Swap to OpenAI/Claude by setting the env var.
"""