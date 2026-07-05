"""
config.py — Central configuration for ChatMind.
All settings are read from environment variables (loaded from .env).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SQLITE_DB_PATH = str(DATA_DIR / "chatmind.db")
CHROMA_PERSIST_PATH = str(DATA_DIR / "chroma")

# ── API Keys ─────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

# ── Model Registry ────────────────────────────────────────────────────────────
# Each entry: provider, model_id, env_key for the API key
MODEL_REGISTRY: dict[str, dict] = {
    "Groq — Llama 3.3 70B (Default)": {
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
        "cost_per_1k_input": 0.0,   # Groq is free-tier
        "cost_per_1k_output": 0.0,
    },
    "Groq — Llama 3.1 8B (Fast)": {
        "provider": "groq",
        "model_id": "llama-3.1-8b-instant",
        "env_key": "GROQ_API_KEY",
        "cost_per_1k_input": 0.0,
        "cost_per_1k_output": 0.0,
    }
}

DEFAULT_MODEL = "Groq — Llama 3.3 70B (Default)"

# ── System Personas ───────────────────────────────────────────────────────────
SYSTEM_PERSONAS: dict[str, str] = {
    "Default Assistant": (
        "You are ChatMind, a helpful, harmless, and honest AI assistant. "
        "Provide clear, accurate, and thoughtful responses."
    ),
    "Creative Writer": (
        "You are ChatMind, a creative writing assistant with a flair for storytelling. "
        "Help users craft compelling narratives, vivid poetry, and engaging content. "
        "Use evocative language, rich descriptions, and creative structure."
    ),
    "Code Expert": (
        "You are ChatMind, an expert software engineer with deep knowledge across all programming languages, "
        "frameworks, and system design. Provide clean, efficient, well-commented code solutions. "
        "Explain your reasoning clearly and suggest best practices."
    ),
    "Academic Researcher": (
        "You are ChatMind, a rigorous academic research assistant. Provide thorough, balanced, "
        "evidence-based responses. Acknowledge uncertainty, present multiple perspectives, "
        "and cite relevant concepts and fields when applicable."
    ),
    "Concise Advisor": (
        "You are ChatMind, a direct and action-oriented advisor. Respond in bullet points and short sentences. "
        "Get to the point immediately. Avoid filler, caveats, and lengthy explanations unless explicitly asked."
    ),
    "Friendly Tutor": (
        "You are ChatMind, a patient and encouraging tutor. Explain concepts step-by-step using "
        "simple language, helpful analogies, and real-world examples. Check understanding and "
        "offer to elaborate on anything unclear."
    ),
    "Socratic Mentor": (
        "You are ChatMind, a Socratic mentor. Guide users to discover answers themselves through "
        "thoughtful questions and gentle nudges. Ask clarifying questions, surface assumptions, "
        "and help users reason through problems independently."
    ),
}

# ── Embedding Settings ────────────────────────────────────────────────────────
EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "huggingface")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── RAG / Chunking ────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))

# ── Retry Settings ────────────────────────────────────────────────────────────
MAX_RETRIES: int = 3
RETRY_BASE_DELAY: float = 1.0
RETRY_MAX_DELAY: float = 10.0
