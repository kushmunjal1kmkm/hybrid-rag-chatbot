"""
ui/styles.py — Dark-mode CSS for ChatMind.
Injected via st.markdown(..., unsafe_allow_html=True) at app startup.
"""


def get_css() -> str:
    return """
<style>
/* ── Google Font ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Design Tokens ───────────────────────────────────────────────────────── */
:root {
    --bg-app:         #0d1117;
    --bg-sidebar:     #161b22;
    --bg-card:        #1c2128;
    --bg-elevated:    #21262d;
    --border:         #30363d;
    --border-subtle:  #21262d;

    --accent:         #2563eb;
    --accent-hover:   #3b82f6;
    --accent-glow:    rgba(37, 99, 235, 0.25);
    --accent-subtle:  rgba(30, 58, 95, 0.6);

    --purple:         #7c3aed;
    --purple-glow:    rgba(124, 58, 237, 0.25);

    --text-primary:   #e6edf3;
    --text-secondary: #8b949e;
    --text-muted:     #6e7681;

    --green:          #4ade80;
    --green-glow:     rgba(74, 222, 128, 0.25);
    --red:            #f87171;
    --yellow:         #fbbf24;

    --radius-sm:  6px;
    --radius-md:  10px;
    --radius-lg:  14px;
    --radius-xl:  18px;
    --radius-2xl: 24px;

    --shadow-md:  0 4px 24px rgba(0,0,0,0.45);
    --shadow-sm:  0 2px 10px rgba(0,0,0,0.3);

    --transition: 0.15s ease;
}

/* ── Reset ───────────────────────────────────────────────────────────────── */
*, *::before, *::after {
    box-sizing: border-box;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── App Shell ───────────────────────────────────────────────────────────── */
.stApp {
    background-color: var(--bg-app) !important;
    color: var(--text-primary) !important;
}

/* Hide Streamlit chrome */
#MainMenu        { visibility: hidden; }
footer           { visibility: hidden; }
header           { visibility: hidden; }
.stDeployButton  { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* Main container */
.main .block-container {
    padding: 1rem 1.5rem 2rem !important;
    max-width: 880px !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] > div {
    background-color: var(--bg-sidebar) !important;
}

/* ── Sidebar Brand Header ─────────────────────────────────────────────────── */
.chatmind-logo {
    padding: 1.2rem 1rem 1rem;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 0.5rem;
}

.chatmind-logo-title {
    font-size: 1.35rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 60%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.chatmind-logo-sub {
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 400;
    margin: 3px 0 0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── Section labels in sidebar ───────────────────────────────────────────── */
.sidebar-section {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    padding: 1rem 1rem 0.3rem;
}

/* ── Chat Messages ────────────────────────────────────────────────────────── */
/* Override Streamlit chat_message container */
[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 0.3rem 0 !important;
    animation: messageSlideIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes messageSlideIn {
    from {
        opacity: 0;
        transform: translateY(10px) scale(0.98);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* User message bubble */
[data-testid="stChatMessage"][data-testid*="user"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(30,58,95,0.7) 0%, rgba(30,64,128,0.7) 100%) !important;
    border: 1px solid rgba(37,99,235,0.25) !important;
    border-radius: var(--radius-xl) !important;
    padding: 0.75rem 1rem !important;
    margin-left: 8% !important;
}

/* Assistant message bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-xl) !important;
    padding: 0.75rem 1rem !important;
    margin-right: 8% !important;
}

/* Avatars */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] {
    background: transparent !important;
    border: none !important;
    font-size: 1.3rem !important;
}

/* Message text */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li {
    font-size: 0.9rem !important;
    line-height: 1.65 !important;
    color: var(--text-primary) !important;
}

/* Code blocks inside messages */
[data-testid="stChatMessage"] code {
    background: rgba(0,0,0,0.4) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.83rem !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace !important;
    color: #a5d6ff !important;
}

[data-testid="stChatMessage"] pre {
    background: #010409 !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
    overflow-x: auto !important;
    margin: 0.5rem 0 !important;
}

[data-testid="stChatMessage"] pre code {
    background: none !important;
    padding: 0 !important;
    color: var(--text-primary) !important;
    font-size: 0.83rem !important;
}

/* ── Chat Input ──────────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-2xl) !important;
    transition: border-color var(--transition), box-shadow var(--transition) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text-primary) !important;
    font-size: 0.9rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.stButton > button {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
    padding: 0.4rem 0.9rem !important;
}

.stButton > button:hover {
    background: var(--bg-card) !important;
    border-color: var(--accent) !important;
    color: var(--accent-hover) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
}

.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 0 16px var(--accent-glow) !important;
}

/* ── Selectbox ───────────────────────────────────────────────────────────── */
.stSelectbox > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    font-size: 0.85rem !important;
}

.stSelectbox > div > div:hover {
    border-color: var(--accent) !important;
}

/* Selectbox dropdown */
[data-baseweb="popover"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}

[data-baseweb="option"] {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    font-size: 0.85rem !important;
}

[data-baseweb="option"]:hover {
    background: var(--bg-card) !important;
}

/* ── Toggle ──────────────────────────────────────────────────────────────── */
.stToggle label {
    color: var(--text-primary) !important;
    font-size: 0.85rem !important;
}

/* ── Metrics ─────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
}

/* ── File Uploader ───────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius-lg) !important;
    transition: border-color var(--transition) !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] > details {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
}

[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {
    border-color: var(--border-subtle) !important;
    margin: 0.5rem 0 !important;
}

/* ── Alerts / Notifications ───────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    font-size: 0.85rem !important;
}

/* ── Download Button ─────────────────────────────────────────────────────── */
.stDownloadButton > button {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: all var(--transition) !important;
}

.stDownloadButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent-hover) !important;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar          { width: 5px; height: 5px; }
::-webkit-scrollbar-track    { background: transparent; }
::-webkit-scrollbar-thumb    { background: var(--bg-elevated); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border); }

/* ── Custom Components (via st.markdown HTML) ────────────────────────────── */

/* Searching indicator */
.cm-searching {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    font-size: 0.8rem;
    color: var(--text-muted);
    margin: 6px 0;
    width: fit-content;
}

.cm-searching-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
    animation: cmPulse 1.2s ease-in-out infinite;
    flex-shrink: 0;
}

@keyframes cmPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.3; transform: scale(0.75); }
}

/* Source citation badge */
.cm-source-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(37,99,235,0.12);
    border: 1px solid rgba(37,99,235,0.3);
    color: #60a5fa;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 20px;
    margin: 3px 3px 0 0;
    white-space: nowrap;
}

/* Document badge */
.cm-doc-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(74,222,128,0.1);
    border: 1px solid rgba(74,222,128,0.25);
    color: var(--green);
    font-size: 0.72rem;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 20px;
    margin: 2px 3px 2px 0;
}

/* Welcome screen */
.cm-welcome {
    text-align: center;
    padding: 4rem 1rem 2rem;
    max-width: 640px;
    margin: 0 auto;
}

.cm-welcome h2 {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.6rem;
}

.cm-welcome p {
    color: var(--text-secondary);
    font-size: 0.95rem;
    line-height: 1.65;
    margin-bottom: 2.5rem;
}

/* Feature card */
.cm-feature-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1rem 1.1rem;
    margin: 0.4rem 0;
    text-align: left;
    transition: all var(--transition);
}

.cm-feature-card:hover {
    border-color: var(--accent);
    background: var(--bg-elevated);
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
}

.cm-feature-card h4 {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 3px;
}

.cm-feature-card p {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin: 0;
    line-height: 1.4;
}

/* Conversation header */
.cm-conv-header {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    padding: 0.5rem 0 0.75rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 0.5rem;
}

/* Status pill */
.cm-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
    white-space: nowrap;
}

.cm-status-online {
    background: rgba(74,222,128,0.1);
    border: 1px solid rgba(74,222,128,0.3);
    color: var(--green);
}

.cm-status-online::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 6px var(--green-glow);
}

/* Tool call indicator */
.cm-tool-call {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(124,58,237,0.08);
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: var(--radius-md);
    font-size: 0.78rem;
    color: #a78bfa;
    margin: 4px 0;
}

.cm-tool-call strong {
    color: #c4b5fd;
    font-weight: 600;
}
</style>
"""
