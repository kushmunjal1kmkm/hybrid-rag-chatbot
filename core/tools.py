"""
core/tools.py — LangChain tool definitions for ChatMind.

Tools exposed:
  • TavilySearch  — real-time web search
  • RetrieverTool — query ChromaDB uploaded documents
"""
import os

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools.retriever import create_retriever_tool

import config


def get_tavily_tool() -> TavilySearchResults:
    """
    Build the Tavily web-search tool.
    Requires TAVILY_API_KEY in env.
    """
    if not config.TAVILY_API_KEY:
        raise ValueError(
            "TAVILY_API_KEY is not set. Add it to your .env file to enable web search."
        )
    os.environ["TAVILY_API_KEY"] = config.TAVILY_API_KEY
    return TavilySearchResults(
        max_results=config.MAX_SEARCH_RESULTS,
        name="tavily_search",
        description=(
            "A real-time web search engine. Use this tool when you need current information, "
            "recent news, live data, or any fact you are not confident about. "
            "Input should be a concise search query string."
        ),
    )


def get_retriever_tool(retriever):
    """
    Wrap a LangChain retriever (backed by ChromaDB) as a named tool
    so the agent can call it to answer questions about uploaded documents.
    """
    return create_retriever_tool(
        retriever,
        name="search_documents",
        description=(
            "Search through documents the user has uploaded (PDFs, text files). "
            "Use this tool whenever the user asks about content from their uploaded files. "
            "Input should be a natural-language query about the document content."
        ),
    )
