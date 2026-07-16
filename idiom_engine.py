"""
Core pipeline: idiom detection/replacement -> paraphrasing -> translation.

Two backends, chosen automatically:
- NVIDIA NIM (build.nvidia.com): used when NVIDIA_API_KEY is set. One hosted LLM
  handles both paraphrasing and translation, with much better quality than the
  original t5-small + googletrans combo.
- Local fallback: works with zero API keys, using a real paraphrase checkpoint
  (humarin/chatgpt_paraphraser_on_t5_base) and deep-translator for translation.

Everything here is UI-agnostic on purpose so it can be reused by a Streamlit
app, a CLI, tests, etc.
"""
import os
import re
import functools

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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").strip()
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
IDIOMS_PATH = os.environ.get(
    "IDIOMS_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "idiomslist.xlsx")
)

LANG_NAMES = {
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
}


def using_nvidia() -> bool:
    """Re-checked live (not cached at import time) so a key entered at runtime
    in the sidebar takes effect without restarting the app."""
    return bool(NVIDIA_API_KEY)


def set_nvidia_key(key: str, model: str | None = None):
    """Allow the frontend to supply a key/model at runtime (e.g. typed into
    the sidebar) instead of only reading from .env."""
    global NVIDIA_API_KEY, NVIDIA_MODEL
    NVIDIA_API_KEY = (key or "").strip()
    if model:
        NVIDIA_MODEL = model
    _nvidia_client.cache_clear()


# ---------------------------------------------------------------------------
# Idiom dictionary
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def load_idioms(path: str = IDIOMS_PATH):
    """Load idiom -> meaning pairs, longest idiom first, so multi-word idioms
    are matched before shorter idioms that happen to be substrings of them
    (e.g. 'cut to the chase' before 'cut')."""
    df = pd.read_excel(path)
    df = df.fillna("")
    df["Idiom"] = df["Idiom"].astype(str).str.strip()
    df["Meaning"] = df["Meaning"].astype(str).str.strip().str.rstrip(".")
    df = df[(df["Idiom"] != "") & (df["Meaning"] != "")]
    pairs = list(dict.fromkeys(zip(df["Idiom"], df["Meaning"])))  # de-dupe, keep order
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def replace_idioms(sentence: str):
    """Replace idiom occurrences with their plain-English meanings.
    Returns (modified_sentence, [(idiom, meaning), ...]) for idioms actually found."""
    modified = sentence
    matched = []
    for idiom, meaning in load_idioms():
        pattern = r"\b{}\b".format(re.escape(idiom))
        if re.search(pattern, modified, flags=re.IGNORECASE):
            modified = re.sub(pattern, meaning, modified, flags=re.IGNORECASE)
            matched.append((idiom, meaning))
    return modified, matched


# ---------------------------------------------------------------------------
# NVIDIA NIM client (lazy)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _nvidia_client():
    from openai import OpenAI

    return OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)


def _nvidia_chat(prompt: str, max_tokens: int, temperature: float) -> str:
    resp = _nvidia_client().chat.completions.create(
        model=NVIDIA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip().strip('"')


# ---------------------------------------------------------------------------
# Local fallback model (lazy — only imports torch/transformers if actually used)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _local_paraphraser():
    from transformers import pipeline

    return pipeline("text2text-generation", model="humarin/chatgpt_paraphraser_on_t5_base")


# ---------------------------------------------------------------------------
# Paraphrasing
# ---------------------------------------------------------------------------
def paraphrase_text(text: str) -> str:
    if not text.strip():
        return text
    if using_nvidia():
        try:
            out = _nvidia_chat(
                "Paraphrase the following sentence in natural English. Keep the "
                "meaning identical. Reply with only the paraphrased sentence, "
                f"nothing else.\n\n{text}",
                max_tokens=120,
                temperature=0.6,
            )
            return out or text
        except Exception as error:
            print("NVIDIA paraphrase error:", error)
            return text
    try:
        result = _local_paraphraser()(f"paraphrase: {text}", max_length=120, num_beams=5, do_sample=False)
        out = result[0].get("generated_text", "").strip()
        return out or text
    except Exception as error:
        print("Local paraphrase error:", error)
        return text


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
def translate_text(text: str, target_language: str = "ta") -> str:
    if not text.strip():
        return text
    lang_name = LANG_NAMES.get(target_language, target_language)
    if using_nvidia():
        try:
            out = _nvidia_chat(
                f"Translate the following sentence into {lang_name}. Reply with "
                f"only the translation, nothing else.\n\n{text}",
                max_tokens=150,
                temperature=0.3,
            )
            return out or text
        except Exception as error:
            print("NVIDIA translation error:", error)
            return text
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="en", target=target_language).translate(text)
    except Exception as error:
        print("Local translation error:", error)
        return text


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
def run_pipeline(sentence: str, target_language: str = "ta") -> dict:
    modified, matched = replace_idioms(sentence)
    paraphrased = paraphrase_text(modified)
    translated = translate_text(paraphrased, target_language)
    return {
        "original": sentence,
        "modified": modified,
        "matched_idioms": matched,
        "paraphrased": paraphrased,
        "translated": translated,
        "engine": "NVIDIA NIM (%s)" % NVIDIA_MODEL if using_nvidia() else "Local models",
    }
