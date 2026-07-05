"""
core/llm_chains.py — LCEL-based chain and agent builders for ChatMind.

Three chain types:
  1. Plain chat chain      — simple conversation with message history (LCEL)
  2. RAG chain             — context injection from ChromaDB + history (LCEL)
  3. Tool-calling agent    — LangGraph create_react_agent with Tavily/retriever tools

NOTE: LangChain >=1.0 removed AgentExecutor and create_tool_calling_agent from
`langchain.agents`. We use:
  - `langgraph.prebuilt.create_react_agent`  for the agent
  - `langchain_classic.agents` as fallback if needed
"""
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

import config
from core.memory import get_message_history


# ─────────────────────────────────────────────────────────────────────────────
# LLM Factory
# ─────────────────────────────────────────────────────────────────────────────

def build_llm(
    model_name: str = config.DEFAULT_MODEL,
    temperature: float = 0.7,
    streaming: bool = True,
):
    """
    Instantiate the appropriate LangChain chat model based on the model registry.
    Raises ValueError if the required API key is missing.
    """
    if model_name not in config.MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name!r}")

    entry = config.MODEL_REGISTRY[model_name]
    provider = entry["provider"]
    model_id = entry["model_id"]
    api_key = os.getenv(entry["env_key"], "")

    if not api_key:
        raise ValueError(
            f"API key not set for {model_name}.\n"
            f"Add  {entry['env_key']}=<your-key>  to your .env file."
        )

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_id,
            groq_api_key=api_key,
            temperature=temperature,
            streaming=streaming,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_id,
            openai_api_key=api_key,
            temperature=temperature,
            streaming=streaming,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_id,
            anthropic_api_key=api_key,
            temperature=temperature,
            streaming=streaming,
        )
    else:
        raise ValueError(f"Unknown provider: {provider!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Chain Builders
# ─────────────────────────────────────────────────────────────────────────────

def _history_runnable(chain):
    """Wrap any LCEL chain with SQLite-backed message history."""
    return RunnableWithMessageHistory(
        chain,
        get_message_history,          # session_id → SQLChatMessageHistory
        input_messages_key="input",
        history_messages_key="history",
    )


def build_chat_chain_with_history(llm, system_prompt: str):
    """
    Simple LCEL chat chain with automatic message history.

    Input dict:  {"input": str}
    Config:      {"configurable": {"session_id": conv_id}}
    Output:      str (streamed)
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    chain = prompt | llm | StrOutputParser()
    return _history_runnable(chain)


def build_rag_chain(llm, retriever, system_prompt: str):
    """
    RAG LCEL chain: retrieves relevant chunks from ChromaDB and injects
    them as context. Instructs the model to cite document sources.

    Input dict:  {"input": str}
    Config:      {"configurable": {"session_id": conv_id}}
    Output:      str (streamed)
    """
    rag_system = (
        system_prompt
        + "\n\n"
        "You have access to retrieved document context below. "
        "Use it to answer the question accurately. "
        "At the end of your response, cite which document(s) and chunk(s) "
        "you used in the format:\n\n"
        "> **Sources:** [filename | Chunk N], [filename | Chunk M]\n\n"
        "If the context doesn't help, say so and answer from your own knowledge.\n\n"
        "--- Retrieved Context ---\n"
        "{context}\n"
        "--- End Context ---"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", rag_system),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    def _format_docs(docs) -> str:
        if not docs:
            return "(No relevant documents found.)"
        parts = []
        for doc in docs:
            src = doc.metadata.get("source", "Unknown")
            idx = doc.metadata.get("chunk_index", "?")
            parts.append(f"[{src} | Chunk {idx}]\n{doc.page_content}")
        return "\n\n".join(parts)

    chain = (
        RunnablePassthrough.assign(
            context=lambda x: _format_docs(retriever.invoke(x["input"]))
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    return _history_runnable(chain)


def build_agent(llm, tools: list, system_prompt: str):
    """
    Build a LangGraph ReAct agent with tool-calling capability.

    Uses langgraph.prebuilt.create_react_agent which is the modern
    recommended approach for LangChain >=1.0 / LangGraph >=1.0.

    Returns a compiled graph that accepts:
      {"messages": [...]} and streams/invokes like a Runnable.
    """
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )
    return agent


# ─────────────────────────────────────────────────────────────────────────────
# Agent invocation helpers (history is managed manually for LangGraph agents)
# ─────────────────────────────────────────────────────────────────────────────

def invoke_agent(agent, user_input: str, history_messages: list, system_prompt: str) -> dict:
    """
    Invoke the LangGraph agent with full message history.

    LangGraph create_react_agent takes a `messages` list directly.
    We pass: [SystemMessage] + history + [HumanMessage(user_input)]

    Returns dict with keys:
      - "output": str        — final assistant text
      - "tool_calls": list   — list of (tool_name, tool_input) tuples
    """
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

    messages = [SystemMessage(content=system_prompt)]
    messages.extend(history_messages)
    messages.append(HumanMessage(content=user_input))

    result = agent.invoke({"messages": messages})
    all_messages = result.get("messages", [])

    # Extract final AI response (last AIMessage with content)
    final_output = ""
    tool_calls_made = []

    for msg in all_messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_made.append({
                    "tool": tc.get("name", ""),
                    "input": tc.get("args", {}),
                })
        if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            final_output = msg.content

    return {
        "output": final_output,
        "tool_calls": tool_calls_made,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Token estimation
# ─────────────────────────────────────────────────────────────────────────────

def estimate_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Estimate token count using tiktoken if available, else rough heuristic.
    The heuristic (len / 4) is accurate to ~±20% for English text.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding(model)
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


# ─────────────────────────────────────────────────────────────────────────────
# Retry wrapper (for non-streaming calls)
# ─────────────────────────────────────────────────────────────────────────────

def invoke_with_retry(chain, inputs: dict, run_config: dict) -> Any:
    """
    Call chain.invoke() with exponential-backoff retry on rate-limit errors.
    Used for agent mode.
    """

    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=config.RETRY_BASE_DELAY,
            min=1,
            max=config.RETRY_MAX_DELAY,
        ),
        reraise=True,
    )
    def _invoke():
        return chain.invoke(inputs, config=run_config)

    return _invoke()
