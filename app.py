"""
app.py — ChatMind main Streamlit application entry point.

Architecture:
  • Sidebar: new-chat button, conversation history, model/persona/toggle settings,
             token stats, export buttons
  • Main area: welcome screen OR active conversation (messages + chat input)
  • Document upload: expandable section above chat
  • Streaming: token-by-token for simple chains, spinner+result for agent

Run:
    streamlit run app.py
"""
import io
import os
import tempfile
from datetime import datetime
from reportlab.platypus import Flowable

import streamlit as st

# ── Page config MUST be first Streamlit call ───────────────────────────────────
st.set_page_config(
    page_title="ChatMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**ChatMind** — Production AI chatbot built with LangChain + Groq",
    },
)

# ── Internal imports (after page config) ──────────────────────────────────────
import config
from core.memory import (
    init_db,
    create_conversation,
    list_conversations,
    get_conversation,
    update_conversation_title,
    update_conversation_stats,
    delete_conversation,
    get_message_history,
    clear_message_history,
)
from core.llm_chains import (
    build_llm,
    build_chat_chain_with_history,
    build_rag_chain,
    build_agent,
    invoke_agent,
    estimate_tokens,
    invoke_with_retry,
)
from core.tools import get_tavily_tool, get_retriever_tool
from core.vector_store import (
    process_uploaded_file,
    get_retriever,
    get_uploaded_docs_for_conversation,
    delete_docs_for_conversation,
)
from ui.styles import get_css
from ui.components import (
    render_sidebar_logo,
    render_sidebar_section,
    render_conversation_list,
    render_token_stats,
    render_conversation_header,
    render_message_history,
    render_searching_indicator,
    render_tool_call_details,
    render_source_badges,
    render_doc_badges,
    render_online_status,
    render_welcome_screen,
    render_api_key_warning,
)

# ── CSS injection ──────────────────────────────────────────────────────────────
st.markdown(get_css(), unsafe_allow_html=True)

# ── DB init ────────────────────────────────────────────────────────────────────
init_db()


# ─────────────────────────────────────────────────────────────────────────────
# Session-state defaults
# ─────────────────────────────────────────────────────────────────────────────

def _init_state() -> None: # most of the default things that are needed for initializing
    defaults: dict = {
        "current_conv_id":    None,
        "selected_model":     config.DEFAULT_MODEL,
        "selected_persona":   "Default Assistant",
        "web_search_enabled": False,
        "rag_enabled":        False,
        "pending_delete":     None,
        "upload_trigger":     0,   # increment to reset file uploader how many files are there for the rag implementation
    }
    for key, val in defaults.items(): # this makes sure that the default things are in the streamlit.session_state if not add it
        if key not in st.session_state:
            st.session_state[key] = val


_init_state()


# ─────────────────────────────────────────────────────────────────────────────
# LLM + chain helpers (cached per model to avoid re-instantiation)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False) # the cache_resource stores the models in cache and return that only if it is asked again without running it again and again makes it faster 
def _get_llm(model_name: str):
    """Cache LLM client instances — cleared when model changes."""
    return build_llm(model_name, temperature=0.7, streaming=True)


def _get_chain(conv_id: str):
    """
    Build the correct chain/agent based on current UI toggles.
    Returns (chain, error_str | None, is_agent: bool).
    """
    model_name = st.session_state.selected_model
    persona    = st.session_state.selected_persona
    system_prompt = config.SYSTEM_PERSONAS[persona]

    try:
        llm = _get_llm(model_name)
    except ValueError as exc:
        return None, str(exc), False

    tools = []
    use_agent = False

    # ── Tavily tool ─────────────────────────────────────────────────────────
    if st.session_state.web_search_enabled and config.TAVILY_API_KEY:
        try:
            tools.append(get_tavily_tool())
            use_agent = True
        except ValueError:
            pass  # key missing warning shown in sidebar

    # ── RAG retriever tool (add to agent OR build dedicated RAG chain) ───────
    if st.session_state.rag_enabled:
        retriever = get_retriever(conv_id)
        if use_agent:
            tools.append(get_retriever_tool(retriever))
        else:
            # Pure RAG chain (no search tool)
            chain = build_rag_chain(llm, retriever, system_prompt)
            return chain, None, False

    if use_agent and tools:
        chain = build_agent(llm, tools, system_prompt)
        return chain, None, True

    # Default: plain chat chain
    chain = build_chat_chain_with_history(llm, system_prompt)
    return chain, None, False


# ─────────────────────────────────────────────────────────────────────────────
# PDF Export helper
# ─────────────────────────────────────────────────────────────────────────────

def _export_pdf(title: str, messages) -> bytes: # exports all the chats to an pdf exporter 
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    ) # makes a simple doc template and write it to buffer first that is in ram for easy workflow

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CM_Title", parent=styles["Heading1"], fontSize=18,
        textColor=colors.HexColor("#1e3a8a"), spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "CM_Meta", parent=styles["Italic"], fontSize=10,
        textColor=colors.HexColor("#6b7280"), spaceAfter=12,
    )
    user_label = ParagraphStyle(
        "CM_User", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#1e40af"), fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=2,
    )
    ai_label = ParagraphStyle(
        "CM_AI", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#065f46"), fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "CM_Body", parent=styles["Normal"], fontSize=10,
        leading=16, textColor=colors.HexColor("#374151"),
    ) # writes many different labels to go with the template to make it informative 
    divider = HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"))

    story : list[Flowable] = []
    story = [
        Paragraph(f"ChatMind — {title}", title_style),
        Paragraph(
            f"Exported {datetime.now().strftime('%Y-%m-%d %H:%M')} · {len(messages)} messages",
            meta_style,
        ),
        divider,
    ]

    for msg in messages:
        role_label = "You" if msg.type == "human" else "ChatMind"
        label_style = user_label if msg.type == "human" else ai_label
        # Sanitise XML special chars for reportlab
        safe = (
            msg.content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        story += [
            Spacer(1, 0.2 * cm),
            Paragraph(role_label, label_style),
            Paragraph(safe, body_style),
            divider,
        ]

    doc.build(story) # build the pdf and write it to buffer
    buffer.seek(0) # start again from the starting
    return buffer.read() # read and return to user 


# ─────────────────────────────────────────────────────────────────────────────
# Markdown Export helper
# ─────────────────────────────────────────────────────────────────────────────

def _export_markdown(conv: dict, messages) -> str:
    lines = [
        f"# {conv.get('title', 'Conversation')}",
        f"",
        f"*Exported from ChatMind on {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Model: {conv.get('model', 'Unknown')} · Turns: {conv.get('message_count', 0)}*",
        f"",
        "---",
        "",
    ]
    for msg in messages:
        role = "**You**" if msg.type == "human" else "**ChatMind**"
        lines += [f"{role}", "", msg.content, "", "---", ""]
    return "\n".join(lines)

# above this all the function are created and below this some are used for ui or to render some other things 
# ─────────────────────────────────────────────────────────────────────────────
# ░░░  SIDEBAR  ░░░░
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    render_sidebar_logo()

    # ── New chat ───────────────────────────────────────────────────────────
    if st.button("✏️  New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
        new_id = create_conversation(
            model=st.session_state.selected_model,
            persona=st.session_state.selected_persona,
        )
        st.session_state.current_conv_id = new_id
        st.rerun()

    # ── Conversation list ──────────────────────────────────────────────────
    render_sidebar_section("Conversations")
    conversations = list_conversations()

    if not conversations:
        st.markdown(
            '<div style="padding:0.6rem 1rem;color:#6e7681;font-size:0.8rem;">'
            "No conversations yet.<br>Click <b>New Chat</b> to start!"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        selected_id, delete_id = render_conversation_list(
            conversations, st.session_state.current_conv_id or ""
        )
        if selected_id and selected_id != st.session_state.current_conv_id:
            st.session_state.current_conv_id = selected_id
            st.rerun()
        if delete_id:
            st.session_state.pending_delete = delete_id
            st.rerun()

    # ── Handle pending delete ──────────────────────────────────────────────
    if st.session_state.pending_delete:
        del_id = st.session_state.pending_delete
        st.session_state.pending_delete = None
        delete_conversation(del_id)
        clear_message_history(del_id)
        delete_docs_for_conversation(del_id)
        if st.session_state.current_conv_id == del_id:
            st.session_state.current_conv_id = None
        st.rerun()

    st.divider()

    # ── Settings ───────────────────────────────────────────────────────────
    render_sidebar_section("Settings")

    new_model = st.selectbox(
        "🤖 Model",
        options=list(config.MODEL_REGISTRY.keys()),
        index=list(config.MODEL_REGISTRY.keys()).index(st.session_state.selected_model),
        key="model_sel",
    )
    if new_model != st.session_state.selected_model: # if a different model is selected then cache is changed and new cache is built 
        st.session_state.selected_model = new_model
        st.cache_resource.clear()   # evict cached LLM

    new_persona = st.selectbox(
        "🎭 Persona",
        options=list(config.SYSTEM_PERSONAS.keys()),
        index=list(config.SYSTEM_PERSONAS.keys()).index(st.session_state.selected_persona),
        key="persona_sel",
    )
    st.session_state.selected_persona = new_persona

    st.session_state.web_search_enabled = st.toggle(
        "🔍 Web Search Mode",
        value=st.session_state.web_search_enabled,
        help="Agent calls Tavily to fetch real-time web results when needed",
        key="web_search_toggle",
    )
    if st.session_state.web_search_enabled and not config.TAVILY_API_KEY:
        st.warning("⚠️ Set TAVILY_API_KEY in .env", icon="🔑")

    st.session_state.rag_enabled = st.toggle(
        "📚 Use Uploaded Docs",
        value=st.session_state.rag_enabled,
        help="Retrieve relevant chunks from ChromaDB to ground answers",
        key="rag_toggle",
    )

    # ── Online status pill ─────────────────────────────────────────────────
    render_online_status(st.session_state.selected_model)

    # ── Stats & Export for current conversation ────────────────────────────
    if st.session_state.current_conv_id:
        cur_conv = get_conversation(st.session_state.current_conv_id)
        if cur_conv:
            st.divider()
            render_sidebar_section("Usage")
            render_token_stats(cur_conv)

            # Export
            history_for_export = get_message_history(st.session_state.current_conv_id)
            msgs_for_export = history_for_export.messages # getting all the messages 

            if msgs_for_export: # means if there are messages 
                st.divider()
                render_sidebar_section("Export")

                md_content = _export_markdown(cur_conv, msgs_for_export) # this function is on the top of this file
                st.download_button(
                    "⬇️ Export as Markdown",
                    data=md_content,
                    file_name=f"chatmind_{cur_conv.get('title','chat')[:30].replace(' ','_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="export_md",
                )

                try:
                    pdf_bytes = _export_pdf(cur_conv.get("title", "Conversation"), msgs_for_export) # this function is on the top of this file
                    st.download_button(
                        "⬇️ Export as PDF",
                        data=pdf_bytes,
                        file_name=f"chatmind_{cur_conv.get('title','chat')[:30].replace(' ','_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="export_pdf",
                    )
                except Exception:
                    pass  # reportlab not installed — skip silently


# ─────────────────────────────────────────────────────────────────────────────
# ░░░  MAIN CONTENT  ░░░
# ─────────────────────────────────────────────────────────────────────────────

# ── Welcome screen ─────────────────────────────────────────────────────────────
if st.session_state.current_conv_id is None: # if there is no conversation selected 
    render_welcome_screen()
    st.markdown("<br>", unsafe_allow_html=True) #br is used for space
    col_l, col_c, col_r = st.columns([1, 2, 1]) # columns are used for spacing
    with col_c:
        if st.button(
            "✏️ Start a New Conversation",
            use_container_width=True,
            type="primary",
            key="welcome_new_chat",
        ):
            new_id = create_conversation(
                model=st.session_state.selected_model,
                persona=st.session_state.selected_persona,
            )
            st.session_state.current_conv_id = new_id
            st.rerun()
    st.stop() # once the above code is executed, no more code will be executed

# ── Validate active conversation ────────────────────────────────────────────────
conv_id  = st.session_state.current_conv_id
conv_row = get_conversation(conv_id)

if conv_row is None:
    # Conversation was deleted externally
    st.session_state.current_conv_id = None
    st.rerun()

# ── Conversation header ─────────────────────────────────────────────────────────
col_hdr, col_clear = st.columns([6, 1]) # 6 parts for header and 1 part for clear button
with col_hdr:
    render_conversation_header(conv_row["title"])
with col_clear:
    if st.button("🗑 Clear", key="clear_btn", help="Erase all messages in this thread"):
        clear_message_history(conv_id)
        st.rerun()

# ── Document upload section ─────────────────────────────────────────────────────
with st.expander("📎 Upload Documents (PDF / TXT)", expanded=False):
    existing_docs = get_uploaded_docs_for_conversation(conv_id)
    render_doc_badges(existing_docs)

    uploaded_file = st.file_uploader(
        "Drop a file here or click to browse",
        type=["pdf", "txt"],
        key=f"uploader_{st.session_state.upload_trigger}",
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        with st.spinner(f"Processing **{uploaded_file.name}**…"):
            ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            try:
                n_chunks = process_uploaded_file(tmp_path, uploaded_file.name, conv_id) # process the file
                st.success(
                    f"✅ **{uploaded_file.name}** indexed — {n_chunks} chunks stored in ChromaDB"
                )

                st.session_state.rag_enabled = True
                st.session_state.upload_trigger += 1 # increment the upload trigger
                st.rerun() # rerun the app
            except ValueError as exc:
                st.error(f"❌ {exc}") # if there is a value error
            except Exception as exc:
                st.error(f"❌ Failed to process file: {exc}") # if there is any other error
            finally:
                try:
                    os.unlink(tmp_path) # remove the temporary file
                except OSError:
                    pass

st.divider()

# ── Render stored message history ───────────────────────────────────────────────
history    = get_message_history(conv_id)
stored_msgs = history.messages
render_message_history(stored_msgs)

# ── Chat input ──────────────────────────────────────────────────────────────────
user_input: str | None = st.chat_input(
    "Message ChatMind…",
    key="chat_input_box",
) # this will give us the input from the user when he hits enter

if not user_input:
    st.stop() # if no message is entered then stop

# ─── From here: user submitted a message ───────────────────────────────────────

# Display user bubble immediately
with st.chat_message("user", avatar="👤"):
    st.markdown(user_input)

# Auto-title from first message
is_first_turn = conv_row.get("message_count", 0) == 0 or conv_row.get("title") == "New Conversation"
if is_first_turn:
    auto_title = user_input.strip()[:60]
    if len(user_input) > 60:
        auto_title += "…"
    update_conversation_title(conv_id, auto_title)
    # Update model/persona on conversation row
    from core.memory import update_conversation_meta
    update_conversation_meta(
        conv_id,
        model=st.session_state.selected_model,
        persona=st.session_state.selected_persona,
    )

# ── Build chain ────────────────────────────────────────────────────────────────
chain, build_error, is_agent = _get_chain(conv_id)
run_cfg = {"configurable": {"session_id": conv_id}}

if build_error:
    with st.chat_message("assistant", avatar="🤖"):
        render_api_key_warning(st.session_state.selected_model, build_error.split("Add")[-1].strip().split(" ")[0])
    st.stop()

assert chain is not None

# ── Generate response ──────────────────────────────────────────────────────────
with st.chat_message("assistant", avatar="🤖"):
    msg_placeholder    = st.empty()
    search_placeholder = st.empty()
    tool_placeholder   = st.empty()

    try:
        # ── Agent mode (Tavily ± retriever via LangGraph) ───────────────────
        if is_agent:
            system_prompt = config.SYSTEM_PERSONAS[st.session_state.selected_persona]

            # Load raw history for LangGraph (list of BaseMessage)
            raw_history = get_message_history(conv_id).messages

            with st.spinner("Thinking…"):
                agent_result = invoke_agent(
                    chain,
                    user_input=user_input,
                    history_messages=raw_history,
                    system_prompt=system_prompt,
                )

            final_answer = agent_result.get("output", "")
            tool_calls   = agent_result.get("tool_calls", [])

            # Show search indicator if search tool was called
            for tc in tool_calls:
                tool_name = tc.get("tool", "")
                if "search" in tool_name.lower():
                    q = tc.get("input", {})
                    if isinstance(q, dict):
                        q = q.get("query", "")
                    search_placeholder.markdown(
                        f'<div class="cm-searching">'
                        f'<div class="cm-searching-dot"></div>'
                        f'🔍 Searched: "{str(q)[:60]}"</div>',
                        unsafe_allow_html=True,
                    )
                    break

            msg_placeholder.markdown(final_answer)

            # Show tool calls summary
            if tool_calls:
                with tool_placeholder:
                    with st.expander(f"🔧 Used {len(tool_calls)} tool(s)", expanded=False):
                        for tc in tool_calls:
                            icon = "🔍" if "search" in tc.get("tool","").lower() else "📄"
                            q = tc.get("input", "")
                            if isinstance(q, dict):
                                q = q.get("query", str(q))
                            st.markdown(
                                f'<div class="cm-tool-call">{icon} <strong>{tc.get("tool","")}</strong>: {str(q)[:80]}</div>',
                                unsafe_allow_html=True,
                            )

            # Manually save to LangChain history (LangGraph manages its own state)
            hist = get_message_history(conv_id)
            from langchain_core.messages import HumanMessage, AIMessage
            hist.add_messages([
                HumanMessage(content=user_input),
                AIMessage(content=final_answer),
            ]) # this is the point where the history is maintained

            tokens_used = estimate_tokens(user_input + final_answer)

        # ── Streaming chat / RAG chain ──────────────────────────────────────
        else:
            full_response = ""
            stream = chain.stream({"input": user_input}, config=run_cfg)
            for chunk in stream:
                if isinstance(chunk, str): # if the chunk is a string
                    full_response += chunk
                elif hasattr(chunk, "content"): # if the chunk has content
                    full_response += chunk.content
                # Live-update with cursor
                msg_placeholder.markdown(full_response + "▌")

            # Final render without cursor
            msg_placeholder.markdown(full_response)
            tokens_used = estimate_tokens(user_input + full_response)

        # ── Update stats ────────────────────────────────────────────────────
        update_conversation_stats(conv_id, tokens_used=tokens_used)
        st.rerun()

    # ── Error handling ──────────────────────────────────────────────────────
    except Exception as exc:
        err = str(exc)
        if any(kw in err.lower() for kw in ("rate_limit", "429", "ratelimit", "too many")):
            msg_placeholder.error(
                "⏳ **Rate limit reached.** Please wait a moment and try again.\n\n"
                "Groq's free tier has per-minute limits — upgrading to a paid plan removes them.",
                icon="⚠️",
            )
        elif any(kw in err.lower() for kw in ("api_key", "authentication", "unauthorized", "invalid key")):
            msg_placeholder.error(
                "🔑 **API key error.** Check your `.env` file.\n\n"
                f"Detail: `{err[:200]}`",
            )
        elif "timeout" in err.lower():
            msg_placeholder.error(
                "⏱️ **Request timed out.** The model may be overloaded — please try again.",
                icon="⚠️",
            )
        else:
            msg_placeholder.error(f"❌ Unexpected error: `{err[:300]}`")

