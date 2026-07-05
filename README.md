# ChatMind — AI Chatbot

> Production-grade AI chatbot built with **Python + Streamlit + LangChain**.  
> Features: streaming responses, persistent multi-thread memory (SQLite),  
> agentic web search (Tavily), document RAG (ChromaDB), dark-mode UI, PDF export.

---

## 🚀 Quick Start

### 1. Clone & enter the directory
```bash
cd ai-chatbot-streamlit
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Note:** First run downloads ~90 MB of sentence-transformer model weights for local embeddings (ChromaDB RAG). This is a one-time download.

### 4. Configure API keys
```bash
copy .env.example .env       # Windows
cp  .env.example .env        # macOS / Linux
```

Open `.env` and fill in your keys:

| Key | Required? | Where to get it |
|-----|-----------|-----------------|
| `GROQ_API_KEY` | ✅ Yes (for default model) | [console.groq.com](https://console.groq.com) — free |
| `TAVILY_API_KEY` | For web search only | [app.tavily.com](https://app.tavily.com) — free tier |
| `OPENAI_API_KEY` | Only for GPT-4o/Mini | [platform.openai.com](https://platform.openai.com) |
| `ANTHROPIC_API_KEY` | Only for Claude models | [console.anthropic.com](https://console.anthropic.com) |

### 5. Run the app
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 📁 Project Structure

```
ai-chatbot-streamlit/
├── app.py                    # Main Streamlit entry point
├── config.py                 # Settings, model registry, API keys
├── requirements.txt
├── README.md
├── .env.example
│
├── core/
│   ├── llm_chains.py         # LCEL chains: chat, RAG, tool-calling agent
│   ├── memory.py             # SQLite-backed conversation + message history
│   ├── tools.py              # Tavily search + ChromaDB retriever tools
│   └── vector_store.py       # ChromaDB init, document processing, retriever
│
├── ui/
│   ├── components.py         # Reusable Streamlit UI components
│   └── styles.py             # Injected dark-mode CSS
│
└── data/                     # Runtime data (auto-created, gitignored)
    ├── chatmind.db           # SQLite database (conversations + messages)
    └── chroma/               # Persistent ChromaDB vector store
```

---

## ✨ Features

### 💬 Streaming Chat
Token-by-token streaming responses using LangChain LCEL + Streamlit's `st.write_stream`.

### 🗂 Multiple Conversation Threads
- Sidebar lists all conversations (persisted to SQLite)  
- Each thread has an auto-generated title from the first message  
- Conversations survive app restarts

### 🔍 Web Search Mode (Agentic)
Toggle **Web Search Mode** in the sidebar. When on:
- A `create_tool_calling_agent` decides *when* to call Tavily  
- A "Searching…" indicator appears during tool calls  
- The agent cites search queries in the response  

### 📄 Document Upload (RAG)
Upload PDF or TXT files in the expandable section above chat:
- Files are chunked (`1000 tokens / 200 overlap`)
- Embedded with `sentence-transformers/all-MiniLM-L6-v2` (local)
- Stored in ChromaDB with per-conversation filters
- Toggle **Use Uploaded Docs** to activate retrieval
- Responses include `**Sources:** [file | Chunk N]` citations

### 🎭 Persona / System Prompt
Pick from 7 pre-built personas in the sidebar dropdown:
Default Assistant, Creative Writer, Code Expert, Academic Researcher, Concise Advisor, Friendly Tutor, Socratic Mentor.

### 🔢 Token Tracking
Each conversation shows total tokens used and number of turns in the sidebar.

### 📤 Export
- **Markdown**: clean text dump with timestamps  
- **PDF**: formatted document via ReportLab  

### 🤖 Multiple LLM Providers
| Model | Provider |
|---|---|
| Llama 3.3 70B (default) | Groq |
| Llama 3.1 8B (fast) | Groq |
| Mixtral 8x7B | Groq |
| GPT-4o | OpenAI |
| GPT-4o Mini | OpenAI |
| Claude 3.5 Sonnet | Anthropic |
| Claude 3 Haiku | Anthropic |

### ⚡ Error Handling
- Exponential backoff retry (via `tenacity`) on rate-limit errors  
- Friendly error messages for auth failures, timeouts, parse errors  
- Graceful fallback — app never crashes on LLM errors

---

## ⚙️ Configuration

All settings are in `.env`. Advanced options:

```env
# Embeddings: "huggingface" (local, default) | "openai" (requires key)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=all-MiniLM-L6-v2

# RAG chunk settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_SEARCH_RESULTS=5
RAG_TOP_K=4
```

---

## 🧪 Testing Each Stage

### Stage 1 — Basic Chat
1. Run `streamlit run app.py`  
2. Set `GROQ_API_KEY` in `.env`  
3. Click "New Chat" → type a message → response streams token-by-token ✅

### Stage 2 — Persistence
1. Send a few messages  
2. **Restart** the app (`Ctrl+C` → `streamlit run app.py`)  
3. Conversations still appear in sidebar, messages still visible ✅

### Stage 3 — Web Search
1. Set `TAVILY_API_KEY` in `.env`  
2. Enable **🔍 Web Search Mode**  
3. Ask: *"What is the latest news about AI today?"*  
4. "Searching the web…" indicator appears, result cites live sources ✅

### Stage 4 — Document RAG
1. Upload a PDF (e.g., a research paper)  
2. Enable **📚 Use Uploaded Docs**  
3. Ask a question about the document's content  
4. Response includes `**Sources:** [filename | Chunk N]` ✅

### Stage 5 — Export
1. Have a conversation  
2. Click **⬇️ Export as Markdown** → downloads `.md` file  
3. Click **⬇️ Export as PDF** → downloads formatted PDF ✅

---

## 🗃 Data Files

All runtime data lives in `data/` (auto-created, add to `.gitignore`):

```
data/
├── chatmind.db      # SQLite: conversations table + LangChain message_store table
└── chroma/          # ChromaDB: embeddings + document chunks (binary)
```

To **reset all data**: delete the `data/` directory and restart.

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.35+ with custom CSS |
| Orchestration | LangChain 0.3 (LCEL) |
| LLM — Primary | Groq API (Llama 3.3 70B) |
| LLM — Alternate | OpenAI GPT-4o, Anthropic Claude 3.5 |
| Memory | `SQLChatMessageHistory` → SQLite |
| Vector Store | ChromaDB (local disk) |
| Embeddings | sentence-transformers (local) / OpenAI |
| Web Search | Tavily Search API |
| Agent | `create_tool_calling_agent` + `AgentExecutor` |
| Retry | tenacity (exponential backoff) |
| PDF Export | ReportLab |

---

## 🐛 Common Issues

**"Module not found" errors**  
→ Make sure your virtualenv is activated: `.venv\Scripts\activate`

**Slow first startup**  
→ HuggingFace model weights downloading (~90 MB). Subsequent starts are instant.

**Chroma errors on Windows**  
→ Ensure you have `Visual C++ Build Tools` installed, or set `EMBEDDING_PROVIDER=openai` and provide `OPENAI_API_KEY`.

**Rate limit on Groq**  
→ Groq free tier has per-minute token limits. Wait 60 seconds or upgrade. ChatMind auto-retries with backoff.
