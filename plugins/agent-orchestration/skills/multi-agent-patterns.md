---

## name: multi-agent-patterns
description: Patterns for coordinating multiple Claude agents — delegation, handoffs, parallel execution, and orchestrator-worker architectures. Load when building systems where multiple agents need to collaborate.

# Multi-Agent Coordination Patterns

## Pattern 1: Orchestrator → Worker

```python
import anthropic

client = anthropic.Anthropic()

# Orchestrator decides which worker to call
def orchestrator(task: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system="""You are an orchestrator. Given a task, respond with JSON:
        {"worker": "backend|frontend|researcher", "subtask": "specific task"}""",
        messages=[{"role": "user", "content": task}]
    )
    decision = json.loads(response.content[0].text)
    return workers[decision["worker"]](decision["subtask"])
```

## Pattern 2: Parallel Workers

```python
import asyncio

async def run_parallel_agents(tasks: list[str]) -> list[str]:
    """Run multiple agents simultaneously"""
    async def run_agent(task: str) -> str:
        # Each agent runs independently
        response = await async_client.messages.create(...)
        return response.content[0].text

    results = await asyncio.gather(*[run_agent(t) for t in tasks])
    return results
```

## Pattern 3: Claude Agent SDK (Subagent Delegation)

```python
# In a Claude Code agent file, use the Agent tool to delegate
# The parent agent spawns a subagent and waits for results
# Subagent has full tool access and independent context
```

## Pattern 4: Sequential Pipeline

```python
# Each step feeds into the next
async def pipeline(input_data: str) -> str:
    # Step 1: Research
    research = await researcher_agent(input_data)

    # Step 2: Architect
    design = await architect_agent(research)

    # Step 3: Build
    code = await backend_agent(design)

    return code
```

## Handoff Protocol

Always include in handoff messages:

```python
handoff_context = {
    "from_agent": "researcher",
    "to_agent": "architect",
    "task": "original task description",
    "findings": "what was discovered",
    "decision_needed": "what architect needs to decide",
    "constraints": ["must use FastAPI", "no OpenAI"]
}
```

## Model Selection for Multi-Agent

- Orchestrator: `claude-sonnet-4-5` (decisions + routing)
- Workers doing complex reasoning: `claude-sonnet-4-5`
- Workers doing simple execution: `claude-haiku-4-5`
- Critical reviews: `claude-opus-4-5`

