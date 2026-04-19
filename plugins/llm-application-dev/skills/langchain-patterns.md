---
name: langchain-patterns
description: LangChain and LangGraph patterns for building LLM applications — chains, agents, RAG, memory, and graph workflows. Load this skill when building anything with LangChain or LangGraph.
---

# LangChain & LangGraph Patterns

## Core Imports
```python
# LangChain
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# LangGraph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
```

## Model Setup (Anthropic only)
```python
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    anthropic_api_key=os.environ["ANTHROPIC_API_KEY"]
)
```

## Basic Chain
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}")
])

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"input": "Hello"})
```

## RAG Chain
```python
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

## LangGraph Stateful Agent
```python
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]

def agent(state: State):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

graph = StateGraph(State)
graph.add_node("agent", agent)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

app = graph.compile(checkpointer=MemorySaver())
```

## Common Patterns
- Use `RunnableParallel` for parallel execution
- Use `RunnableLambda` to wrap any Python function
- Always add `.with_retry()` on external calls
- Use `astream_events` for streaming in production
