"""
ui/components.py — Reusable Streamlit UI components for ChatMind.
"""
import html as html_lib
from datetime import datetime
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar components
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar_logo() -> None:
    st.sidebar.markdown(
        """
        <div class="chatmind-logo">
            <div class="chatmind-logo-title">🧠 ChatMind</div>
            <div class="chatmind-logo-sub">Powered by LangChain + Groq</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_section(label: str) -> None:
    st.sidebar.markdown(
        f'<div class="sidebar-section">{label}</div>',
        unsafe_allow_html=True,
    )


def render_conversation_list(
    conversations: list[dict],
    current_conv_id: str,
) -> tuple[str | None, str | None]:
    """
    Render conversation list buttons in sidebar.
    Returns (selected_conv_id, conv_id_to_delete) — both may be None.
    """
    selected = None
    to_delete = None

    for conv in conversations:
        is_active = conv["id"] == current_conv_id
        title = conv.get("title", "New Conversation")
        msg_count = conv.get("message_count", 0)
        updated = (conv.get("updated_at") or "")[:10]

        icon = "💬" if is_active else "🗨️"
        label = f"{icon} {title}"

        col_btn, col_del = st.sidebar.columns([5, 1])
        with col_btn:
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                label,
                key=f"conv_btn_{conv['id']}",
                use_container_width=True,
                type=btn_type,
                help=f"{msg_count} turns · {updated}",
            ):
                selected = conv["id"]
        with col_del:
            if st.button(
                "🗑",
                key=f"conv_del_{conv['id']}",
                help="Delete conversation",
            ):
                to_delete = conv["id"]

    return selected, to_delete


def render_token_stats(conv: dict) -> None:
    """Show message count and token usage as metrics in sidebar."""
    col1, col2 = st.sidebar.columns(2)
    col1.metric("💬 Turns", conv.get("message_count", 0))
    col2.metric("🔢 Tokens", f"{conv.get('total_tokens', 0):,}")


# ─────────────────────────────────────────────────────────────────────────────
# Chat area components
# ─────────────────────────────────────────────────────────────────────────────

def render_conversation_header(title: str) -> None:
    st.markdown(
        f'<div class="cm-conv-header">💬 {html_lib.escape(title)}</div>',
        unsafe_allow_html=True,
    )


def render_message_history(messages) -> None:
    """Replay stored message history in the chat area."""
    for msg in messages:
        role = "user" if msg.type == "human" else "assistant"
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg.content)


def render_searching_indicator(query: str = "") -> None:
    """Animated 'Searching the web...' pill."""
    escaped_q = html_lib.escape(query[:60])
    query_text = f' &ldquo;{escaped_q}&rdquo;' if query else ""
    st.markdown(
        f"""
        <div class="cm-searching">
            <div class="cm-searching-dot"></div>
            🔍 Searching the web{query_text}&hellip;
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tool_call_details(intermediate_steps: list) -> None:
    """Show collapsible tool call details (agent mode)."""
    if not intermediate_steps:
        return

    tool_summaries = []
    for step in intermediate_steps:
        action = step[0]
        tool_name = getattr(action, "tool", "unknown")
        tool_input = getattr(action, "tool_input", "")
        if isinstance(tool_input, dict):
            query = tool_input.get("query", str(tool_input))
        else:
            query = str(tool_input)
        tool_summaries.append((tool_name, query[:80]))

    if tool_summaries:
        with st.expander(f"🔧 Used {len(tool_summaries)} tool(s)", expanded=False):
            for name, query in tool_summaries:
                icon = "🔍" if "search" in name.lower() else "📄"
                st.markdown(
                    f'<div class="cm-tool-call">{icon} <strong>{name}</strong>: {html_lib.escape(query)}</div>',
                    unsafe_allow_html=True,
                )


def render_source_badges(sources: list[str]) -> None:
    """Render document source citation badges."""
    if not sources:
        return
    badges = "".join(
        f'<span class="cm-source-badge">📎 {html_lib.escape(s)}</span>'
        for s in sources
    )
    st.markdown(
        f'<div style="margin-top:6px;line-height:2">{badges}</div>',
        unsafe_allow_html=True,
    )


def render_doc_badges(docs: list[str]) -> None:
    """Show uploaded document name badges."""
    if not docs:
        return
    badges = "".join(
        f'<span class="cm-doc-badge">📄 {html_lib.escape(d)}</span>'
        for d in docs
    )
    st.markdown(
        f'<div style="margin-bottom:8px;line-height:2.2">{badges}</div>',
        unsafe_allow_html=True,
    )


def render_online_status(model_name: str) -> None:
    short = model_name.split("—")[-1].strip() if "—" in model_name else model_name
    st.sidebar.markdown(
        f'<div style="padding:0 1rem 0.5rem">'
        f'<span class="cm-status-pill cm-status-online">online · {html_lib.escape(short)}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Welcome screen
# ─────────────────────────────────────────────────────────────────────────────

_FEATURES = [
    ("🔍 Real-time Web Search", "Enable Web Search Mode for up-to-date info via Tavily"),
    ("📄 Document Analysis",    "Upload PDFs & text files for intelligent Q&A with citations"),
    ("🧠 Persistent Memory",    "All conversations saved to SQLite — survive restarts"),
    ("🤖 Multiple Models",      "Switch between Groq Llama, GPT-4o, Claude, and more"),
    ("🎭 Custom Personas",      "Choose a persona/tone from the sidebar dropdown"),
    ("📤 Export Chats",         "Download conversations as Markdown or PDF"),
]


def render_welcome_screen() -> None:
    st.markdown(
        """
        <div class="cm-welcome">
            <h2>Welcome to ChatMind ✨</h2>
            <p>
                A production-grade AI assistant with real-time web search,<br>
                document analysis, persistent memory, and streaming responses.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, (title, desc) in enumerate(_FEATURES):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="cm-feature-card">
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# API key warning
# ─────────────────────────────────────────────────────────────────────────────

def render_api_key_warning(model_name: str, env_key: str) -> None:
    st.error(
        f"**API Key Missing** — `{env_key}` is not set.\n\n"
        f"Copy `.env.example` → `.env` and add your key to use **{model_name}**.",
        icon="🔑",
    )
