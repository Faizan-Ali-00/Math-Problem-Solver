import re
import json
import os
import base64
import requests
from io import BytesIO
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from solver import solve_math, normalize_math_input
from explainer import explain_solution, explain_definition, solve_from_image
from diagrams import (
    plot_function, plot_triangle, plot_circle, plot_implicit,
    plot_shape, plot_tangent, plot_semicircle, plot_inscribed_triangle
)

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Numera — Solve Any Math Problem",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# LOGO — Numera (π in a Circle)
# =========================

LOGO_SVG = """
<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="numGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1"/>
      <stop offset="50%" stop-color="#8b5cf6"/>
      <stop offset="100%" stop-color="#ec4899"/>
    </linearGradient>
    <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#818CF8"/>
      <stop offset="50%" stop-color="#A78BFA"/>
      <stop offset="100%" stop-color="#F472B6"/>
    </linearGradient>
    <filter id="numGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="7" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="720" height="240" fill="#0b0715" rx="24"/>

  <g transform="translate(120, 120)">
    <circle cx="0" cy="0" r="82" fill="url(#numGrad)" filter="url(#numGlow)"/>
    <circle cx="0" cy="0" r="72" fill="none" stroke="#ffffff" stroke-opacity="0.25" stroke-width="2"/>
    <text x="0" y="28" font-family="Georgia, 'Times New Roman', serif"
          font-size="82" font-weight="700" fill="#ffffff"
          text-anchor="middle">π</text>
  </g>

  <text x="245" y="132"
        font-family="'Inter','Segoe UI',Arial,Helvetica,sans-serif"
        font-size="72" font-weight="900"
        fill="url(#textGrad)"
        letter-spacing="-3">Numera</text>

  <text x="250" y="176"
        font-family="'Inter','Segoe UI',Arial,Helvetica,sans-serif"
        font-size="14" font-weight="500"
        fill="#b8b2d6"
        letter-spacing="3">SOLVE · LEARN · UNDERSTAND</text>

  <circle cx="555" cy="124" r="6" fill="#F472B6" opacity="0.95"/>
</svg>
"""

ICON_SVG = """
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="numGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1"/>
      <stop offset="50%" stop-color="#8b5cf6"/>
      <stop offset="100%" stop-color="#ec4899"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="44" fill="#0b0715"/>
  <circle cx="100" cy="100" r="78" fill="url(#numGrad2)"/>
  <circle cx="100" cy="100" r="68" fill="none" stroke="#ffffff" stroke-opacity="0.22" stroke-width="2"/>
  <text x="100" y="128" font-family="Georgia, 'Times New Roman', serif"
        font-size="72" font-weight="700" fill="#ffffff" text-anchor="middle">π</text>
</svg>
"""


def svg_to_data_uri(svg_string: str) -> str:
    encoded = base64.b64encode(svg_string.strip().encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


LOGO_DATA_URI = svg_to_data_uri(LOGO_SVG)
ICON_DATA_URI = svg_to_data_uri(ICON_SVG)

# =========================
# STORAGE
# =========================

HISTORY_FILE = Path("history.json")
SETTINGS_FILE = Path("settings.json")

DEFAULT_SETTINGS = {
    "level": "Matric",
    "temperature": 0.3,
    "max_tokens": 1500,
}


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def add_history_entry(kind, question, answer, level):
    entry = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
        "timestamp": datetime.now().strftime("%b %d, %Y · %H:%M"),
        "kind": kind,
        "question": question[:300],
        "answer": answer[:600],
        "level": level,
    }
    history = load_history()
    history.insert(0, entry)
    history = history[:50]
    save_history(history)
    return entry


def delete_history_entry(entry_id):
    history = load_history()
    history = [h for h in history if h["id"] != entry_id]
    save_history(history)


def clear_history():
    save_history([])


def load_settings():
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings_file(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


# =========================
# SESSION STATE
# =========================

if "settings" not in st.session_state:
    st.session_state.settings = load_settings()
if "settings_saved_msg" not in st.session_state:
    st.session_state.settings_saved_msg = False
if "settings_reset_msg" not in st.session_state:
    st.session_state.settings_reset_msg = False
if "settings_version" not in st.session_state:
    st.session_state.settings_version = 0

# =========================
# API KEYS (for sidebar display)
# =========================

def _get_secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return default


GROQ_API_KEY = _get_secret("GROQ_API_KEY")
GEMINI_API_KEY = _get_secret("GEMINI_API_KEY")
CEREBRAS_API_KEY = _get_secret("CEREBRAS_API_KEY")
OPENROUTER_API_KEY = _get_secret("OPENROUTER_API_KEY")

# =========================
# CSS
# =========================

st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at 15% 5%, #6366f111 0%, transparent 45%),
            radial-gradient(circle at 85% 95%, #ec489911 0%, transparent 45%),
            linear-gradient(180deg, #0b0715 0%, #0f0c29 100%);
        background-attachment: fixed;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}

    .hero {
        display: flex;
        justify-content: center;
        padding: 1rem 0 0.4rem 0;
    }
    .hero img {
        width: 100%;
        max-width: 440px;
        height: auto;
        filter: drop-shadow(0 20px 50px rgba(139, 92, 246, 0.35));
    }

    .desc-block {
        text-align: center;
        max-width: 640px;
        margin: 0.5rem auto 1.2rem auto;
        padding: 0 1rem;
    }
    .desc-tagline {
        font-size: 1.15rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .desc-text {
        color: #94a3b8;
        font-size: 0.92rem;
        line-height: 1.6;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(139, 92, 246, 0.15);
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #8b5cf6; }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div { color: #d8d3f0; }
    section[data-testid="stSidebar"] small,
    section[data-testid="stSidebar"] .stCaption { color: #8b84b5 !important; }

    section[data-testid="stSidebar"] button[data-baseweb="tab"] {
        background: transparent !important; color: #8b84b5 !important;
        font-weight: 600 !important; font-size: 0.82rem !important;
        padding: 0.5rem 0.6rem !important; border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] button[data-baseweb="tab"][aria-selected="true"] {
        color: #8b5cf6 !important; background: rgba(139, 92, 246, 0.1) !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tab-list"] {
        background: rgba(15, 17, 21, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 12px !important;
        padding: 0.25rem !important;
        gap: 0.15rem !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tab-highlight"] { display: none !important; }
    section[data-testid="stSidebar"] div[data-baseweb="tab-border"] { display: none !important; }

    .side-brand {
        display: flex; align-items: center; gap: 0.7rem;
        padding: 0.4rem 0.3rem 1.2rem 0.3rem;
        border-bottom: 1px solid rgba(139, 92, 246, 0.15);
        margin-bottom: 1rem;
    }
    .side-logo {
        width: 38px; height: 38px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.45);
    }
    .side-logo img { width: 38px; height: 38px; display: block; }
    .side-brand-text h3 {
        font-size: 1rem; font-weight: 800; margin: 0; line-height: 1.1;
        background: linear-gradient(90deg, #818CF8, #A78BFA, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.3px;
    }
    .side-brand-text p {
        font-size: 0.62rem; color: #8b84b5; margin: 1px 0 0 0;
        letter-spacing: 0.6px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white; border: none; border-radius: 12px;
        padding: 0.85rem 1.6rem; font-weight: 700; font-size: 0.95rem;
        transition: all 0.3s ease; width: 100%;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.35);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(236, 72, 153, 0.5);
    }

    section[data-testid="stSidebar"] .stButton > button {
        background: #1c1f26 !important;
        color: #d8d3f0 !important;
        border: 1px solid #2a2f3a !important;
        box-shadow: none !important;
        padding: 0.55rem 1rem !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        transform: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #8b5cf6 !important;
        color: #c4b5fd !important;
        background: #1f232b !important;
    }

    .stTextInput input,
    .stTextArea textarea {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 12px !important;
        color: #e0e0e8 !important;
        font-size: 1rem !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    }

    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(139, 92, 246, 0.25) !important;
        border-radius: 10px !important;
        color: #e0e0e8 !important;
    }

    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #8b84b5 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.7rem 1.3rem !important;
        border-radius: 10px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #c4b5fd !important;
        background: rgba(139, 92, 246, 0.12) !important;
    }
    div[data-baseweb="tab-list"] {
        background: rgba(15, 17, 21, 0.5) !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        border-radius: 14px !important;
        padding: 0.35rem !important;
        gap: 0.2rem !important;
        justify-content: center;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    div[data-baseweb="tab-border"] { display: none !important; }

    div[data-testid="stImage"] img {
        border-radius: 14px;
        border: 1px solid rgba(139, 92, 246, 0.25);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    }

    .result-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(236, 72, 153, 0.05) 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-left: 4px solid #8b5cf6;
        border-radius: 16px;
        padding: 1.6rem 1.8rem;
        margin: 1rem 0;
        color: #e0e0e8;
        font-size: 1.02rem;
        line-height: 1.8;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
    }

    .hist-card {
        background: rgba(15, 17, 21, 0.7);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.6rem;
    }
    .hist-time { font-size: 0.68rem; color: #8b84b5; font-weight: 600; margin-bottom: 0.3rem; }
    .hist-question {
        font-size: 0.85rem; color: #e0e0e8; font-weight: 600;
        line-height: 1.4; margin-bottom: 0.35rem;
        display: -webkit-box; -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden;
    }
    .hist-answer {
        font-size: 0.78rem; color: #94a3b8; line-height: 1.4;
        display: -webkit-box; -webkit-line-clamp: 2;
        -webkit-box-orient: vertical; overflow: hidden;
    }
    .hist-tag {
        display: inline-block;
        padding: 0.12rem 0.45rem;
        background: rgba(139, 92, 246, 0.12);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 4px;
        font-size: 0.62rem;
        color: #c4b5fd;
        font-weight: 600;
        margin-top: 0.4rem;
    }

    .side-section-title {
        font-size: 0.68rem; color: #8b84b5; text-transform: uppercase;
        letter-spacing: 1.5px; font-weight: 700; margin: 1rem 0 0.6rem 0;
    }

    .side-empty {
        text-align: center;
        padding: 1.5rem 0.5rem;
        color: #64748b;
        font-size: 0.82rem;
    }
    .side-empty-icon { font-size: 1.8rem; opacity: 0.4; margin-bottom: 0.5rem; }

    .success-banner {
        background: linear-gradient(135deg, rgba(16,185,129,0.15) 0%, rgba(139,92,246,0.1) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 10px;
        padding: 0.7rem 0.9rem;
        color: #4ade80;
        font-weight: 600;
        font-size: 0.8rem;
        margin-bottom: 0.8rem;
    }

    .provider-badge {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(236,72,153,0.12));
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 999px;
        font-size: 0.78rem;
        color: #c4b5fd;
        font-weight: 700;
        margin: 0.5rem 0 1rem 0;
        letter-spacing: 0.3px;
    }

    p, span, div, label { color: #d8d3f0; }
    .stCaption, small { color: #8b84b5 !important; }
    .stSpinner > div { border-top-color: #8b5cf6 !important; }
    .stAlert { border-radius: 12px; }

    hr { border-color: rgba(139, 92, 246, 0.1); margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# =========================
# DIAGRAM RENDERER
# =========================

def render_diagram_from_hint(text):
    inscribed_match = re.search(r"PLOTINSCRIBED:\s*([\d.\-]+\s*,\s*[\d.\-]+(?:\s*;\s*[\d.\-]+\s*,\s*[\d.\-]+){2})", text)
    shape_match = re.search(r"PLOTSHAPE:\s*([\d.\-]+\s*,\s*[\d.\-]+(?:\s*;\s*[\d.\-]+\s*,\s*[\d.\-]+)+)", text)
    tangent_match = re.search(r"PLOTTANGENT:\s*([\-\d.]+)\s*,\s*([\-\d.]+)\s*,\s*([\d.]+)\s*,\s*([\-\d.]+)\s*,\s*([\-\d.]+)", text)
    semicircle_match = re.search(r"PLOTSEMICIRCLE:\s*([\-\d.]+)\s*,\s*([\-\d.]+)\s*,\s*([\d.]+)\s*,\s*(upper|lower|left|right)", text, re.IGNORECASE)
    circle_match = re.search(r"PLOTCIRCLE:\s*([\-\d.]+)\s*,\s*([\-\d.]+)\s*,\s*([\d.]+)", text)
    triangle_match = re.search(r"PLOTTRIANGLE:\s*([\d.]+)\s*,\s*([\d.]+)", text)
    implicit_match = re.search(r"PLOTIMPLICIT:\s*(.+)", text)
    func_match = re.search(r"PLOTFUNC:\s*(.+)", text)

    try:
        if inscribed_match:
            pairs = inscribed_match.group(1).split(';')
            vertices = []
            for pair in pairs:
                vx, vy = pair.split(',')
                vertices.append((float(vx.strip()), float(vy.strip())))
            st.subheader("📊 Diagram")
            st.pyplot(plot_inscribed_triangle(vertices))

        elif shape_match:
            pairs = shape_match.group(1).split(';')
            vertices = []
            for pair in pairs:
                vx, vy = pair.split(',')
                vertices.append((float(vx.strip()), float(vy.strip())))
            st.subheader("📊 Diagram")
            st.pyplot(plot_shape(vertices))

        elif tangent_match:
            h, k, r, px, py = tangent_match.groups()
            st.subheader("📊 Diagram")
            st.pyplot(plot_tangent(h, k, r, px, py))

        elif semicircle_match:
            h, k, r, orientation = semicircle_match.groups()
            st.subheader("📊 Diagram")
            st.pyplot(plot_semicircle(h, k, r, orientation.lower()))

        elif circle_match:
            h, k, r = circle_match.groups()
            st.subheader("📊 Diagram")
            st.pyplot(plot_circle(h, k, r))

        elif triangle_match:
            a, b = triangle_match.groups()
            st.subheader("📊 Diagram")
            st.pyplot(plot_triangle(a, b))

        elif implicit_match:
            expr_hint = implicit_match.group(1).strip()
            if expr_hint.upper() != "NONE":
                st.subheader("📊 Diagram")
                st.pyplot(plot_implicit(expr_hint))

        elif func_match:
            expr_hint = func_match.group(1).strip()
            if expr_hint.upper() != "NONE":
                st.subheader("📊 Diagram")
                st.pyplot(plot_function(expr_hint))

    except Exception:
        st.info("Couldn't auto-generate a diagram for this example.")


# =========================
# SIDEBAR
# =========================

with st.sidebar:
    st.markdown(
        f"""
        <div class="side-brand">
            <div class="side-logo"><img src="{ICON_DATA_URI}" alt="Numera" /></div>
            <div class="side-brand-text">
                <h3>Numera</h3>
                <p>SOLVE · LEARN · UNDERSTAND</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_create, tab_history, tab_settings = st.tabs(["🧮 Solve", "📚 History", "⚙️ Settings"])

    with tab_create:
        st.markdown('<div class="side-section-title">Your Level</div>', unsafe_allow_html=True)
        level = st.selectbox(
            "Level",
            ["Matric", "Intermediate", "BS"],
            index=["Matric", "Intermediate", "BS"].index(st.session_state.settings["level"]),
            label_visibility="collapsed",
            key="side_level"
        )

        st.markdown("---")
        st.caption("💡 Type naturally: x², x^2, or x**2 all work the same.")

        active = []
        if GROQ_API_KEY: active.append("Groq")
        if GEMINI_API_KEY: active.append("Gemini")
        if CEREBRAS_API_KEY: active.append("Cerebras")
        if OPENROUTER_API_KEY: active.append("OpenRouter")
        st.caption(f"🔗 Active: {' · '.join(active) if active else 'None'}")

    with tab_history:
        history = load_history()

        if not history:
            st.markdown(
                """
                <div class="side-empty">
                    <div class="side-empty-icon">📚</div>
                    <div>No problems solved yet</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="side-section-title">{len(history)} solved</div>',
                unsafe_allow_html=True
            )

            if st.button("🗑️  Clear All", use_container_width=True, key="side_clear_all"):
                clear_history()
                st.rerun()

            st.markdown("")

            for idx, entry in enumerate(history):
                st.markdown(
                    f"""
                    <div class="hist-card">
                        <div class="hist-time">🕐 {entry['timestamp']} · {entry['kind']}</div>
                        <div class="hist-question">{entry['question']}</div>
                        <div class="hist-answer">{entry['answer']}</div>
                        <span class="hist-tag">{entry['level']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.expander("View / Delete", expanded=False):
                    st.markdown(f"**Question:** {entry['question']}")
                    st.markdown(f"**Answer:** {entry['answer']}")
                    if st.button("🗑️ Delete", key=f"del_{idx}_{entry['id']}", use_container_width=True):
                        delete_history_entry(entry['id'])
                        st.rerun()

    with tab_settings:
        if st.session_state.settings_saved_msg:
            st.markdown('<div class="success-banner">✅ Settings saved</div>', unsafe_allow_html=True)
            st.session_state.settings_saved_msg = False

        if st.session_state.settings_reset_msg:
            st.markdown('<div class="success-banner">✅ Reset to defaults</div>', unsafe_allow_html=True)
            st.session_state.settings_reset_msg = False

        v = st.session_state.settings_version

        st.markdown('<div class="side-section-title">Default Level</div>', unsafe_allow_html=True)
        new_level = st.radio(
            "Default Level",
            options=["Matric", "Intermediate", "BS"],
            index=["Matric", "Intermediate", "BS"].index(st.session_state.settings["level"]),
            horizontal=False,
            label_visibility="collapsed",
            key=f"settings_level_v{v}"
        )

        st.markdown('<div class="side-section-title">Temperature</div>', unsafe_allow_html=True)
        new_temp = st.slider(
            "Temperature",
            min_value=0.0, max_value=1.0,
            value=float(st.session_state.settings["temperature"]),
            step=0.05,
            label_visibility="collapsed",
            key=f"settings_temp_v{v}"
        )
        st.caption(f"Current: **{new_temp}**")

        st.markdown('<div class="side-section-title">Max Tokens</div>', unsafe_allow_html=True)
        new_tokens = st.slider(
            "Max Tokens",
            min_value=500, max_value=3000,
            value=int(st.session_state.settings["max_tokens"]),
            step=100,
            label_visibility="collapsed",
            key=f"settings_tokens_v{v}"
        )
        st.caption(f"Current: **{new_tokens}** tokens")

        st.markdown("")

        if st.button("💾  Save Settings", use_container_width=True, key=f"save_settings_v{v}"):
            st.session_state.settings["level"] = new_level
            st.session_state.settings["temperature"] = new_temp
            st.session_state.settings["max_tokens"] = new_tokens
            save_settings_file(st.session_state.settings)
            st.session_state.settings_saved_msg = True
            st.rerun()

        if st.button("↺  Reset to Defaults", use_container_width=True, key=f"reset_settings_v{v}"):
            st.session_state.settings = DEFAULT_SETTINGS.copy()
            save_settings_file(DEFAULT_SETTINGS)
            st.session_state.settings_version += 1
            for k in list(st.session_state.keys()):
                if k.startswith("side_") or k.startswith("settings_"):
                    try:
                        del st.session_state[k]
                    except Exception:
                        pass
            st.session_state.settings_reset_msg = True
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="side-section-title">Currently Saved</div>', unsafe_allow_html=True)

        current = st.session_state.settings
        st.markdown(
            f"""
            <div style="font-size:0.82rem;line-height:1.9;">
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#94a3b8;">Level</span>
                    <strong style="color:#c4b5fd;">{current['level']}</strong>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#94a3b8;">Temp</span>
                    <strong style="color:#c4b5fd;">{current['temperature']}</strong>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#94a3b8;">Tokens</span>
                    <strong style="color:#c4b5fd;">{current['max_tokens']}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# HERO + DESCRIPTION
# =========================

st.markdown(
    f"""
    <div class="hero">
        <img src="{LOGO_DATA_URI}" alt="Numera logo" />
    </div>
    <div class="desc-block">
        <div class="desc-tagline">Solve · Learn · Understand</div>
        <div class="desc-text">
            Numera solves equations, explains step-by-step, and reads math problems from photos —
            built for Matric, Intermediate, and BS students.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# MAIN TABS
# =========================

tab1, tab2, tab3 = st.tabs(["🧮 Solve a Problem", "📖 Understand a Definition", "📷 Snap & Solve"])

# ---------- TAB 1: SOLVE ----------
with tab1:
    st.subheader("Enter your equation or expression")
    question = st.text_input(
        "Enter your equation or expression",
        placeholder="e.g. x² - 5x + 6 = 0",
        key="solve_input",
        help="You can type it naturally: x², 2x, x^2 — all work.",
        label_visibility="collapsed"
    )

    if st.button("Solve", type="primary", key="solve_btn"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Solving..."):
                try:
                    normalized_question = normalize_math_input(question)
                    result = solve_math(question)

                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.subheader("✅ Answer")
                    if result["type"] == "equation":
                        st.write(f"**Solutions:** {', '.join(result['solutions'])}")
                    else:
                        st.write(f"**Simplified:** {result['simplified']}")
                        st.write(f"**Derivative:** {result['derivative']}")
                        st.write(f"**Integral:** {result['integral']}")
                    st.markdown('</div>', unsafe_allow_html=True)

                    with st.spinner("Preparing explanation..."):
                        explanation, provider = explain_solution(question, result, level)

                    st.markdown(
                        f'<span class="provider-badge">⚡ Answered by {provider}</span>',
                        unsafe_allow_html=True
                    )

                    st.subheader("📖 Step-by-Step Explanation")
                    st.write(explanation)

                    if result["type"] != "equation":
                        st.subheader("📊 Graph")
                        fig = plot_function(normalized_question)
                        st.pyplot(fig)
                    else:
                        render_diagram_from_hint(explanation)

                    add_history_entry(
                        "Solve",
                        question,
                        result.get("solutions", [result.get("simplified", "See explanation")])[0]
                        if result["type"] == "equation"
                        else result.get("simplified", "See explanation"),
                        level
                    )

                except Exception as e:
                    st.error(f"Couldn't process that. Try format like: x**2 - 5*x + 6 = 0\n\nError: {e}")

# ---------- TAB 2: DEFINITION ----------
with tab2:
    st.subheader("Enter a math term or concept")
    term = st.text_input(
        "Enter a math term or concept",
        placeholder="e.g. derivative, matrix, standard deviation",
        key="def_input",
        label_visibility="collapsed"
    )

    if st.button("Explain", type="primary", key="def_btn"):
        if not term.strip():
            st.warning("Please enter a term first.")
        else:
            with st.spinner("Preparing explanation..."):
                explanation, provider = explain_definition(term, level)

            st.markdown(
                f'<span class="provider-badge">⚡ Answered by {provider}</span>',
                unsafe_allow_html=True
            )

            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.write(explanation)
            st.markdown('</div>', unsafe_allow_html=True)

            render_diagram_from_hint(explanation)

            add_history_entry("Definition", term, explanation, level)

# ---------- TAB 3: CAMERA ----------
with tab3:
    st.subheader("Take a photo of your math question")
    st.caption("Works best with clear handwriting or printed text, good lighting, no shadows on the paper.")

    img_source = st.radio("Choose input method", ["📷 Camera", "🖼️ Upload Image"], horizontal=True)

    image_data = None
    if img_source == "📷 Camera":
        camera_photo = st.camera_input("Take a picture of the question")
        if camera_photo:
            image_data = camera_photo.getvalue()
    else:
        uploaded_img = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_img:
            image_data = uploaded_img.getvalue()
            st.image(uploaded_img, caption="Uploaded question", use_container_width=True)

    if image_data:
        if st.button("Solve from Image", type="primary", key="img_solve_btn"):
            with st.spinner("Reading and solving..."):
                try:
                    result, provider = solve_from_image(image_data, level)

                    st.markdown(
                        f'<span class="provider-badge">⚡ Answered by {provider}</span>',
                        unsafe_allow_html=True
                    )

                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.write(result)
                    st.markdown('</div>', unsafe_allow_html=True)

                    add_history_entry("Image", "Photo uploaded", result, level)

                except Exception as e:
                    st.error(f"Couldn't process the image. Try a clearer photo. Error: {e}")

# =========================
# FOOTER
# =========================

st.markdown("---")
st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.5rem 0; color:#8b84b5; font-size:0.8rem;">
        <img src="{ICON_DATA_URI}" style="width:18px;height:18px;border-radius:5px;opacity:0.85;" />
        <span>Numera · Solve · Learn · Understand</span>
    </div>
    """,
    unsafe_allow_html=True
)
