"""
Idiom Replacer & Translator — Streamlit frontend.

Run with:  streamlit run app.py
"""
import streamlit as st

import idiom_engine as engine

st.set_page_config(
    page_title="Idiom Bridge",
    page_icon="🌉",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system — injected once
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

:root {
    --paper: #F7F4EE;
    --ink: #24211C;
    --teal: #0E5A57;
    --teal-dark: #0A3F3D;
    --marigold: #E4A339;
    --plum: #5C3A57;
    --line: #DAD2C2;
    --card: #FFFFFF;
}

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.stApp { background: var(--paper); color: var(--ink); }

/* Hide default streamlit chrome bits that fight the design */
#MainMenu, footer, header { visibility: hidden; }

.block-container { padding-top: 2.5rem; max-width: 760px; }

/* ---- Header ---- */
.ib-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--teal);
    margin-bottom: 0.3rem;
}
.ib-title {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: 2.6rem;
    line-height: 1.05;
    color: var(--ink);
    margin: 0 0 0.4rem 0;
}
.ib-title em { color: var(--teal); font-style: normal; }
.ib-tagline {
    font-size: 1.02rem;
    color: #5A554C;
    margin-bottom: 1.8rem;
    max-width: 46ch;
}

/* ---- Pipeline stepper (signature element) ---- */
.ib-stepper {
    display: flex;
    align-items: stretch;
    gap: 0;
    margin: 1.6rem 0 2rem 0;
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    background: var(--card);
}
.ib-step {
    flex: 1;
    padding: 0.85rem 0.6rem;
    text-align: center;
    border-right: 1px solid var(--line);
    position: relative;
}
.ib-step:last-child { border-right: none; }
.ib-step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #A79E8C;
    letter-spacing: 0.08em;
}
.ib-step-label {
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 0.15rem;
    color: #8A8272;
}
.ib-step.active { background: var(--teal); }
.ib-step.active .ib-step-num { color: #BFE0DD; }
.ib-step.active .ib-step-label { color: white; }

/* ---- Cards ---- */
.ib-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-left: 4px solid var(--teal);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.9rem;
}
.ib-card.accent { border-left-color: var(--marigold); }
.ib-card.plum { border-left-color: var(--plum); }
.ib-card-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9A9284;
    margin-bottom: 0.35rem;
}
.ib-card-text { font-size: 1.02rem; line-height: 1.5; }
.ib-card-text.tamil { font-size: 1.15rem; }

/* ---- Idiom chips ---- */
.ib-chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.6rem 0 1.2rem 0; }
.ib-chip {
    font-size: 0.8rem;
    background: #FBF0DC;
    color: var(--teal-dark);
    border: 1px solid #EFDBAE;
    border-radius: 999px;
    padding: 0.25rem 0.7rem;
    font-family: 'IBM Plex Mono', monospace;
}
.ib-chip b { color: var(--ink); font-family: 'Inter', sans-serif; font-weight: 600; }

/* ---- Buttons / inputs ---- */
.stButton>button {
    background: var(--teal);
    color: white;
    border: none;
    border-radius: 7px;
    padding: 0.55rem 1.6rem;
    font-weight: 600;
    font-size: 0.95rem;
}
.stButton>button:hover { background: var(--teal-dark); color: white; }

textarea { border-radius: 8px !important; }

.ib-engine-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #6E6858;
    margin-top: -0.6rem;
    margin-bottom: 1.4rem;
}
.ib-engine-badge b { color: var(--teal); }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Settings")

    nvidia_key_input = st.text_input(
        "NVIDIA API key (optional)",
        value=engine.NVIDIA_API_KEY,
        type="password",
        help="Get a free key at build.nvidia.com. Leave blank to run fully offline "
        "with local models instead.",
    )
    nvidia_model_input = st.text_input(
        "NVIDIA model",
        value=engine.NVIDIA_MODEL,
        help="Any chat model available on build.nvidia.com, e.g. "
        "meta/llama-3.1-8b-instruct or nvidia/llama-3.1-nemotron-70b-instruct.",
    )
    if nvidia_key_input != engine.NVIDIA_API_KEY or nvidia_model_input != engine.NVIDIA_MODEL:
        engine.set_nvidia_key(nvidia_key_input, nvidia_model_input)

    st.markdown("---")

    target_language = st.selectbox(
        "Translate to",
        options=list(engine.LANG_NAMES.keys()),
        format_func=lambda code: f"{engine.LANG_NAMES[code]} ({code})",
        index=0,
    )

    st.markdown("---")
    engine_label = "NVIDIA NIM ⚡" if engine.using_nvidia() else "Local models (offline)"
    st.caption(f"**Active engine:** {engine_label}")
    if not engine.using_nvidia():
        st.caption(
            "No API key set — paraphrasing runs on a local T5 checkpoint and "
            "translation uses deep-translator. Both work with zero cost, just "
            "slower and lower quality than NVIDIA NIM."
        )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="ib-eyebrow">Idiom → Meaning → Translation</div>', unsafe_allow_html=True)
st.markdown('<h1 class="ib-title">Idiom <em>Bridge</em></h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="ib-tagline">Type an English sentence full of idioms. '
    "It gets untangled into plain English, paraphrased, and translated — "
    "so meaning survives the trip across languages.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
sentence = st.text_area(
    "Your sentence",
    placeholder="e.g. Don't beat around the bush, just cut to the chase.",
    height=120,
    label_visibility="collapsed",
)
run = st.button("Process sentence →")

# ---------------------------------------------------------------------------
# Pipeline + results
# ---------------------------------------------------------------------------
if run:
    if not sentence.strip():
        st.warning("Type a sentence first.")
    else:
        with st.spinner("Untangling idioms, paraphrasing, translating…"):
            result = engine.run_pipeline(sentence, target_language)

        stages = ["Original", "Idioms replaced", "Paraphrased", "Translated"]
        stepper_html = '<div class="ib-stepper">'
        for i, label in enumerate(stages, start=1):
            stepper_html += (
                f'<div class="ib-step active"><div class="ib-step-num">{i:02d}</div>'
                f'<div class="ib-step-label">{label}</div></div>'
            )
        stepper_html += "</div>"
        st.markdown(stepper_html, unsafe_allow_html=True)

        if result["matched_idioms"]:
            chips = "".join(
                f'<div class="ib-chip"><b>{idiom}</b> → {meaning}</div>'
                for idiom, meaning in result["matched_idioms"]
            )
            st.markdown(f'<div class="ib-chip-row">{chips}</div>', unsafe_allow_html=True)
        else:
            st.caption("No idioms from the dataset were detected in this sentence.")

        st.markdown(
            f"""<div class="ib-card">
                <div class="ib-card-label">Modified — idioms replaced</div>
                <div class="ib-card-text">{result['modified']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="ib-card accent">
                <div class="ib-card-label">Paraphrased</div>
                <div class="ib-card-text">{result['paraphrased']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="ib-card plum">
                <div class="ib-card-label">Translation — {engine.LANG_NAMES.get(target_language, target_language)}</div>
                <div class="ib-card-text tamil">{result['translated']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="ib-engine-badge">Powered by <b>{result["engine"]}</b></div>',
            unsafe_allow_html=True,
        )
