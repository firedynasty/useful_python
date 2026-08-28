"""
RAG Chat — conversational interface against any local RAG knowledge base.

Usage:
    streamlit run rag_chat.py
"""

import os
import sys
import glob
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RAG Chat", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    "<style>[data-testid='collapsedControl'] { display: none; }</style>",
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

APPS_DIR = os.path.dirname(os.path.abspath(__file__))


def find_rag_folders() -> list[str]:
    return [
        os.path.basename(p)
        for p in sorted(glob.glob(os.path.join(APPS_DIR, "*")))
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "rag_config.toml"))
    ]


def load_rag(folder_name: str):
    rag_path = folder_name if os.path.isabs(folder_name) else os.path.join(APPS_DIR, folder_name)
    if rag_path not in sys.path:
        sys.path.insert(0, rag_path)
    for mod in ["src.retrieval", "src.constants", "src"]:
        sys.modules.pop(mod, None)
    from src.retrieval import get_knowledge_base, get_context
    from src.constants import get_rag_config
    return get_knowledge_base, get_context, get_rag_config


def get_rag_context(gkb, gc, grc, query: str) -> str:
    config = grc()
    k_base = gkb()
    return gc(
        k_base=k_base,
        query_text=query,
        n_retrieve=config["retriever"]["n_retrieve"],
        n_titles=config["retriever"]["n_titles"],
        enrich_first=config["retriever"]["enrich_first"],
    )


# ── Copy-last JS ──────────────────────────────────────────────────────────────

def copy_button_html(text: str, label: str = "Copy", btn_id: str = "copybtn") -> str:
    safe = text.replace("\\", "\\\\").replace("`", "\\`")
    return f"""
<div style="display:inline-flex;align-items:center;height:2.2rem;">
<button id="{btn_id}" style="padding:0.3rem 0.9rem;border-radius:8px;
  border:1px solid rgba(49,51,63,0.3);background:transparent;cursor:pointer;
  font-family:sans-serif;font-size:0.85rem;color:#31333F;">{label}</button>
<style>
@media (prefers-color-scheme: dark) {{
  #{btn_id} {{ color:#FAFAFA; border-color:rgba(250,250,250,0.3); }}
}}
</style>
</div>
<script>
document.getElementById('{btn_id}').addEventListener('click', async () => {{
  try {{
    await window.parent.navigator.clipboard.writeText(`{safe}`);
    document.getElementById('{btn_id}').textContent = 'Copied \u2713';
    setTimeout(() => document.getElementById('{btn_id}').textContent = '{label}', 1500);
  }} catch(e) {{
    document.getElementById('{btn_id}').textContent = 'Press \u2318C';
    setTimeout(() => document.getElementById('{btn_id}').textContent = '{label}', 2500);
  }}
}});
</script>
"""


# ── Sidebar ───────────────────────────────────────────────────────────────────

_env_key = os.getenv("OPENAI_API_KEY", "")

with st.sidebar:
    st.header("Settings")

    st.subheader("OpenAI API Key")
    if _env_key:
        st.success("Key loaded from environment.")
        api_key = _env_key
    else:
        api_key = st.text_input("OpenAI API Key:", type="password")

    st.divider()

    st.subheader("Knowledge Base")
    rag_folders = find_rag_folders()

    dropdown_choice = st.selectbox(
        "RAG folder (auto-detected)",
        ["— select —"] + rag_folders if rag_folders else ["— none found —"],
        label_visibility="collapsed",
    )

    custom_path = st.text_input(
        "Or enter any RAG folder path:",
        placeholder="/path/to/rag_myfolder",
    )

    if custom_path.strip():
        selected_rag = custom_path.strip().rstrip("/")
        if not os.path.exists(selected_rag):
            st.error(f"Path not found: {selected_rag}")
            selected_rag = None
        elif not os.path.exists(os.path.join(selected_rag, "rag_config.toml")):
            st.error("Not a valid RAG folder (missing rag_config.toml)")
            selected_rag = None
    elif dropdown_choice not in ("— select —", "— none found —"):
        selected_rag = dropdown_choice
    else:
        selected_rag = None

    st.divider()

    st.subheader("Model")
    model = st.selectbox(
        "model",
        ["gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"],
        label_visibility="collapsed",
    )

    st.divider()

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.contexts = []
        st.rerun()

    st.caption(
        "RAG retrieves relevant chunks for each question, "
        "then the full conversation history is sent to the model."
    )

# ── Session state ─────────────────────────────────────────────────────────────

st.session_state.setdefault("messages", [])   # {"role": "user"|"assistant", "content": str}
st.session_state.setdefault("contexts", [])   # retrieved context per user turn

# ── Header ────────────────────────────────────────────────────────────────────

st.title("RAG Chat")
if selected_rag:
    st.caption(f"Knowledge base: **{selected_rag}**")

if not api_key:
    st.info("Enter your OpenAI API key in the sidebar, or set OPENAI_API_KEY in your shell.")

# ── Render conversation history ───────────────────────────────────────────────

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Copy button on assistant messages
        if msg["role"] == "assistant":
            components.html(copy_button_html(msg["content"], "Copy", f"copy_{i}"), height=36)
        # Expandable context on user turns
        if msg["role"] == "user" and i // 2 < len(st.session_state.contexts):
            ctx = st.session_state.contexts[i // 2]
            if ctx:
                with st.expander("Retrieved context"):
                    st.text(ctx)

# ── Chat input ────────────────────────────────────────────────────────────────

question = st.chat_input("Ask a question…")

if question:
    if not api_key:
        st.warning("Add your OpenAI API key in the sidebar first.")
        st.stop()
    if not selected_rag:
        st.warning("Select a RAG knowledge base in the sidebar first.")
        st.stop()

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Retrieve RAG context for this question
    with st.spinner("Retrieving context…"):
        try:
            gkb, gc, grc = load_rag(selected_rag)
            context = get_rag_context(gkb, gc, grc, question)
            st.session_state.contexts.append(context)
        except Exception as e:
            st.error(f"RAG retrieval error: {e}")
            st.session_state.messages.pop()
            st.stop()

    # Build messages for API: inject context into system prompt
    system_prompt = (
        "You are a helpful assistant with access to a knowledge base. "
        "Use the provided context to answer questions. "
        "You also have the full conversation history — refer back to it when relevant. "
        "If the context doesn't cover a question, say so clearly.\n\n"
        f"[Context for this question]\n{context}\n[End Context]"
    )

    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    # Stream response
    with st.chat_message("assistant"):
        try:
            from openai import OpenAI, AuthenticationError
            client = OpenAI(api_key=api_key)

            stream = client.chat.completions.create(
                model=model,
                messages=api_messages,
                stream=True,
            )
            answer = st.write_stream(stream)

        except AuthenticationError:
            st.error("Invalid API key.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

        components.html(copy_button_html(answer, "Copy", f"copy_new"), height=36)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
