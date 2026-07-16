# Idiom Bridge

Type an English sentence full of idioms → they get replaced with plain-English
meanings → paraphrased → translated into Tamil (or another language).

Built with a pure-Python frontend ([Streamlit](https://streamlit.io)) — no HTML,
CSS, or JS files required.

## How it works

```
Your sentence
    │
    ▼
1. Idiom replacement   — matched against a 2000+ idiom dataset (idiomslist.xlsx)
    │
    ▼
2. Paraphrasing        — smooths the sentence into natural English
    │
    ▼
3. Translation         — into Tamil (or any of the supported languages)
```

Steps 2 and 3 run on one of two backends, chosen automatically:

| | NVIDIA NIM (recommended) | Local (no API key) |
|---|---|---|
| Paraphrasing | Any chat model on [build.nvidia.com](https://build.nvidia.com) (default `meta/llama-3.1-8b-instruct`) | `humarin/chatgpt_paraphraser_on_t5_base` via 🤗 Transformers |
| Translation | Same NIM model, prompted to translate | `deep-translator` (Google Translate) |
| Cost | Free tier available at build.nvidia.com | Free, fully offline |
| Quality | Noticeably better — handles idiom nuance well | Good enough for a demo |
| First run | Instant | Downloads a ~1GB model the first time |

You don't need to configure anything to switch — the app checks whether an
NVIDIA API key is present (via `.env` or typed into the sidebar) and picks the
right backend automatically.

## Setup

```bash
git clone <this-repo>
cd idiom-replacer
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

### Option A — with NVIDIA NIM (recommended)

1. Get a free API key at [build.nvidia.com](https://build.nvidia.com).
2. Copy `.env.example` to `.env` and paste your key:
   ```
   NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxx
   ```
3. Run the app (below). You can also paste the key directly into the sidebar
   at runtime instead of using `.env`.

### Option B — fully offline, no API key

Just skip the `.env` step. The app will use local models automatically. The
first paraphrase request will download the local model (~1GB), so it'll be
slow once and fast after that.

If you don't want the heavyweight `torch`/`transformers` dependency at all,
remove those lines from `requirements.txt` — the app still runs, it will just
skip paraphrasing (pass the idiom-replaced sentence straight to translation)
if the local model isn't installed.

### Run it

```bash
streamlit run app.py
```

Streamlit will open the app at `http://localhost:8501`.

## Project structure

```
idiom-replacer/
├── app.py              # Streamlit UI (the whole frontend)
├── idiom_engine.py      # Pipeline logic: idiom matching, paraphrasing, translation
├── idiomslist.xlsx      # Idiom → meaning dataset (2000+ entries)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Customizing

- **Add more languages:** add an entry to `LANG_NAMES` in `idiom_engine.py`
  (language-code keys work for both backends as long as `deep-translator`
  supports the code).
- **Swap the NVIDIA model:** change `NVIDIA_MODEL` in `.env` or the sidebar to
  any chat model listed on build.nvidia.com, e.g.
  `nvidia/llama-3.1-nemotron-70b-instruct` for higher quality at more cost/latency.
- **Add more idioms:** just add rows to `idiomslist.xlsx` with `Idiom` and
  `Meaning` columns — no code changes needed.

## Notes on what changed from the original prototype

- Removed the hardcoded Windows path (`D:\idiom_replacer_project\...`) —
  the spreadsheet now loads from the project folder via a relative path.
- Replaced `googletrans` (unofficial, prone to breaking) with `deep-translator`
  for the offline path, and an LLM prompt for the NVIDIA path.
- Replaced generic `t5-small` (not fine-tuned for paraphrasing) with a model
  actually trained for the task, or an LLM prompt.
- Idioms are now matched longest-first so multi-word idioms aren't partially
  shadowed by shorter overlapping ones.
- Sentence truncation bug (`clean_explanation` cutting text at the first `.`
  or `;`) is removed — meanings are cleaned once at load time instead.
- Swapped the Flask + HTML/CSS frontend for a single-file Streamlit UI.
