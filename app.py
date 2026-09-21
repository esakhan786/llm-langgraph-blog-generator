import os
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from graph import build_blog_graph


st.set_page_config(
    page_title="AI Blog Generator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
        :root {
            --bg: #071421;
            --panel: #0d1b2a;
            --panel-2: #122334;
            --accent: #8b5cf6;
            --accent-2: #6ee7b7;
            --text: #edf6ff;
            --muted: #b8c6d9;
            --border: rgba(255,255,255,0.08);
        }

        .stApp {
            background: linear-gradient(135deg, #071421 0%, #0b1220 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1rem 0.5rem 0.5rem 0.5rem;
        }

        .title {
            font-size: 3rem;
            font-weight: 800;
            letter-spacing: -0.05em;
            margin-bottom: 0.25rem;
        }

        .subtitle {
            font-size: 1.05rem;
            color: var(--muted);
            margin-bottom: 1.5rem;
        }

        .card {
            background: linear-gradient(180deg, rgba(18,35,52,0.9), rgba(11,18,32,0.95));
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.2rem;
            box-shadow: 0 14px 40px rgba(0,0,0,0.22);
            margin-bottom: 1rem;
        }

        .review-box {
            background: rgba(10, 16, 28, 0.85);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1rem 1.2rem;
            margin-top: 0.8rem;
        }

        .final-output {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 1.2rem;
            white-space: pre-wrap;
            line-height: 1.75;
        }

        [data-testid="stButton"] button {
            background: linear-gradient(90deg, #7c3aed, #8b5cf6);
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            padding: 0.7rem 1.2rem;
        }

        [data-testid="stButton"] button:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
        }

        .success-banner {
            background: rgba(16,185,129,0.10);
            border: 1px solid rgba(16,185,129,0.28);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            color: #d8fbe9;
            margin-top: 0.5rem;
        }

        .info-banner {
            background: rgba(139,92,246,0.10);
            border: 1px solid rgba(139,92,246,0.30);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            color: #efe7ff;
        }

        textarea {
            border-radius: 12px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Helpers ----------
def init_graph():
    if "graph" not in st.session_state:
        st.session_state.graph = build_blog_graph()
    return st.session_state.graph


def get_config():
    if "config" not in st.session_state:
        st.session_state.config = {
            "configurable": {"thread_id": f"blog-{uuid4().hex[:8]}"}
        }
    return st.session_state.config


def generate_blog(topic, audience, tone):
    graph = init_graph()
    config = get_config()

    st.session_state.graph = graph
    st.session_state.config = config
    st.session_state.interrupt_payload = None
    st.session_state.final_blog = None
    st.session_state.action_status = None
    st.session_state.action_type = None

    try:
        graph.invoke(
            {
                "topic": topic,
                "audience": audience,
                "tone": tone,
            },
            config=config,
        )

        state = graph.get_state(config)

        if getattr(state, "interrupts", None):
            st.session_state.interrupt_payload = state.interrupts[0].value
        else:
            if state.values:
                st.session_state.final_blog = state.values.get("final_blog")
            st.session_state.interrupt_payload = None

        return True

    except Exception as e:
        st.error(f"Blog generation failed: {e}")
        return False


def resume_graph(action: str, feedback: str = ""):
    graph = st.session_state.get("graph")
    config = st.session_state.get("config")

    if not graph or not config:
        st.warning("Please generate a blog first.")
        return None

    try:
        result = graph.invoke(
            Command(resume={"action": action, "feedback": feedback}),
            config=config,
        )

        st.session_state.final_blog = result.get("final_blog")
        st.session_state.interrupt_payload = None

        if action == "approve":
            st.session_state.action_status = (
                "Feedback approved. You can now ask for the next topic or request another blog."
            )
            st.session_state.action_type = "approve"
        elif action == "revise":
            st.session_state.action_status = (
                "Feedback received. I will revise according to your comments. You can ask for the next topic now."
            )
            st.session_state.action_type = "revise"

        return result

    except Exception as e:
        st.error(f"Resume failed: {e}")
        return None


def render_interrupt_payload(payload):
    if not payload:
        return

    st.markdown('<div class="review-box">', unsafe_allow_html=True)
    st.subheader("Review Draft")
    st.caption("The workflow paused so you can approve or revise the generated content.")

    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"stage", "topic", "audience"}:
                continue

            title = str(key).replace("_", " ").title()

            if isinstance(value, str) and value.strip():
                st.markdown(f"### {title}")
                st.write(value)

            elif isinstance(value, (dict, list)):
                st.markdown(f"### {title}")
                st.json(value)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------- Main UI ----------
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown('<div class="title">AI Blog Generator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Generate a blog article, review it, and approve or revise it with feedback.</div>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    with st.form("blog_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_input(
                "Blog Topic",
                placeholder="Example: What is machine learning?",
                help="Enter the main topic for the blog.",
            )

        with col2:
            audience = st.text_input(
                "Target Audience",
                placeholder="Example: AI developers",
                help="Who is the blog written for?",
            )

        tone = st.selectbox(
            "Writing Tone",
            ["Professional", "Technical", "Friendly", "Beginner-friendly", "Persuasive"],
        )

        submitted = st.form_submit_button("Generate Blog", use_container_width=True)

        if submitted:
            if not topic.strip() or not audience.strip():
                st.warning("Please enter both a topic and audience.")
            else:
                ok = generate_blog(topic, audience, tone)
                if ok:
                    st.markdown(
                        '<div class="success-banner">Draft generated successfully. Review it below and choose approve or revise.</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Review / Feedback Section ----------
if st.session_state.get("interrupt_payload"):
    render_interrupt_payload(st.session_state["interrupt_payload"])

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Give Feedback")

    feedback = st.text_area(
        "Revision notes",
        placeholder="Example: Make it more beginner-friendly and add a simple real-world example.",
        height=140,
    )

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Approve Draft", use_container_width=True):
            result = resume_graph("approve", "")
            if result:
                st.rerun()

    with col_b:
        if st.button("Revise Draft", use_container_width=True):
            result = resume_graph("revise", feedback)
            if result:
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Final Output ----------
if st.session_state.get("final_blog"):
    st.markdown("### Final Blog Post")
    st.markdown('<div class="final-output">', unsafe_allow_html=True)
    st.write(st.session_state["final_blog"])
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("action_status"):
        st.markdown(
            f"""
            <div class="info-banner">
                {st.session_state['action_status']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.download_button(
        label="Download as .txt",
        data=st.session_state["final_blog"],
        file_name="blog_post.txt",
        mime="text/plain",
        use_container_width=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Ask for the next blog")

    next_topic = st.text_input("Next Topic", placeholder="Example: AI in healthcare")
    next_audience = st.text_input("Audience", placeholder="Example: startup founders")
    next_tone = st.selectbox(
        "Next Tone",
        ["Professional", "Technical", "Friendly", "Beginner-friendly", "Persuasive"],
        key="next_tone",
    )

    if st.button("Generate Next Blog", use_container_width=True):
        if next_topic.strip():
            generate_blog(next_topic, next_audience.strip() or "general readers", next_tone)
            st.rerun()
        else:
            st.warning("Please enter a next topic.")

    st.markdown("</div>", unsafe_allow_html=True)

else:
    if not st.session_state.get("interrupt_payload"):
        st.markdown(
            """
            <div class="info-banner">
                Generate a blog to start the workflow. After the draft is created, you can review it and approve or revise it.
            </div>
            """,
            unsafe_allow_html=True,
        )