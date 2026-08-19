# AI Code Reviewer

A Streamlit app that reviews pasted source code with Gemini before it reaches a human reviewer. It focuses on **readability, structure, maintainability, correctness, and security**, and streams a compact, high-signal review back to the UI.

This is a **pre-review assistant**, not a replacement for code review. It is meant to catch obvious issues, surface high-impact risks, and suggest tests so a human can spend time on design and intent.

## Features

- Paste code and pick a language from a supported list
- Streams the model response into the page as it is generated
- Uses a fixed review rubric so output stays scannable and consistent
- Keeps the Gemini API key out of source control via Streamlit secrets
- Validates empty submissions before calling the model

## How it works

```text
Browser (Streamlit UI)
        │
        │  language + pasted code
        ▼
    app.py
        │
        │  builds prompt = SYSTEM_PROMPT + language + fenced code
        ▼
    Gemini (gemini-3.5-flash-lite)
        │
        │  streamed text chunks
        ▼
    "AI Review" panel
```

1. The user selects a language and pastes code in the text area.
2. Clicking **Review Code** checks that the snippet is not empty.
3. `review_code()` in `app.py` wraps the snippet with the rubric from `prompt.py`.
4. The app calls `client.models.generate_content_stream(...)` so tokens appear incrementally via `st.write_stream`.
5. The model returns a structured markdown review (assessment, issues, improvements, tests).

The prompt is intentionally constrained: short sections, hard item limits, no invented problems, and no full rewrites. That keeps latency and noise down for a first-pass review.

## Project layout

```text
ai-code-reviewer/
├── app.py              # Streamlit UI, Gemini client, streaming review
├── prompt.py           # SYSTEM_PROMPT: review rubric and output format
├── requirements.txt    # Runtime dependencies
├── .streamlit/
│   └── secrets.toml    # Local API key (not committed)
├── .gitignore          # Ignores venv, .streamlit/, caches
└── README.md
```

| File | Role |
|------|------|
| `app.py` | Page config, language selector, input, streaming call, error handling |
| `prompt.py` | Isolated system prompt so the rubric can change without touching UI code |
| `requirements.txt` | `streamlit` and `google-genai` |
| `.streamlit/secrets.toml` | `GEMINI_API_KEY` for local runs |

## Prerequisites

- Python 3.10+ (the project has been run on Python 3.14)
- A [Google AI Studio](https://aistudio.google.com/apikey) API key for Gemini
- A virtual environment (recommended)

## Quick start

```bash
cd ai-code-reviewer
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create Streamlit secrets (do **not** commit this file):

```bash
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
GEMINI_API_KEY = "your-gemini-api-key"
EOF
```

Run the app:

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Using the app

1. Choose the **Programming Language** that matches the snippet. The language is injected into the prompt and used for the fenced code block, so a mismatch can produce weaker or misleading findings.
2. Paste a focused unit of code: a function, class, or small module. Large dumps dilute the review and hit the compact-output limits in the prompt.
3. Click **Review Code**.
4. Read the streamed **AI Review** from top to bottom. Treat **Critical Issues** as the first things to fix; treat **Improvements** as optional follow-up.

If the text area is empty, the app shows an error and does not call the API. If Gemini fails (bad key, quota, network), the UI shows a generic message plus the exception details.

### What a review contains

The model is instructed to use this shape:

| Section | Purpose |
|---------|---------|
| **Overall Assessment** | Verdict (ready / needs work / not ready), 1–2 strengths, 1–2 highest-impact gaps |
| **Critical Issues** | At most 3 definite problems, each with why it matters and one concrete fix |
| **Improvements** | At most 5 prioritized, actionable changes |
| **What's Good** | At most 3 strengths so the review is not only negative |
| **Suggested Refactoring** | Optional small snippet only when it clarifies a better approach |
| **Recommended Tests** | At most 3 high-value cases or edge conditions |

Typical target length is under ~400 words. Nitpicks are skipped unless they hide a real bug.

### Supported languages

Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, and SQL.

The model is general-purpose, so other languages may still get useful comments if you pick the closest option, but the fenced block language tag will be wrong.

## Configuration

### API key

`app.py` reads:

```python
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
```

Local development uses `.streamlit/secrets.toml`. On Streamlit Community Cloud (or similar), set the same key in the app’s secrets UI instead of a file.

Never put the key in `app.py`, environment screenshots, or git. `.gitignore` already excludes `.streamlit/`.

### Model

The model id is a constant in `app.py`:

```python
MODEL = "gemini-3.5-flash-lite"
```

Flash-lite is a good default for this UI: low latency, cheap enough for interactive streaming, and adequate for a structured pre-review. Swap the string if you want a stronger model for harder languages or deeper security analysis. Keep one model in code so reviews stay comparable.

### Review rubric

Edit `prompt.py` to change tone, section limits, or extra focus areas (for example, accessibility or performance). Keep the prompt:

- Specific about structure so the UI stays easy to scan
- Honest about uncertainty (definite bugs vs suggestions)
- Bounded (item caps and a word target) so streaming stays fast

Avoid stuffing the prompt with generic “be a helpful assistant” text. The current prompt is the product: it is what makes output consistent.

## Best practices

### For running this app

- **Use a venv.** Keep `streamlit` and `google-genai` isolated from system Python.
- **Store secrets only in Streamlit secrets.** Do not export the API key into the shell if you can avoid it; `st.secrets` is the path this app expects.
- **Pin versions when you share the project.** `requirements.txt` currently lists packages without versions. For reproducible installs, pin after a known-good run, for example `pip freeze > requirements.lock` or add `streamlit==…` and `google-genai==…`.
- **Do not commit** `.streamlit/`, `venv/`, `__pycache__/`, or `.cursor/`. Those paths are already ignored.
- **Treat review output as untrusted markdown.** The app renders whatever the model streams. Do not paste secrets, production credentials, or private customer data into the text area.

### For getting useful reviews

- **Review a diff-sized snippet**, not an entire repository. The prompt forbids rewriting the whole application and caps findings; a 20-line function reviews better than a 2,000-line file.
- **Match the language dropdown** to the code. Naming, idioms, and security notes are language-specific.
- **Paste code that compiles or is close to it.** Incomplete fragments cause the model to invent context.
- **Use the review as a checklist**, then verify. Models miss issues and sometimes over-claim. Critical items still need a human to confirm.
- **Iterate.** Apply the critical fixes, paste again, and look for remaining gaps. That matches how you would use a linter plus a teammate.

### For extending the app

- Keep **UI in `app.py`** and **instructions in `prompt.py`**. Mixing them makes prompt iteration harder.
- Prefer **streaming** (`generate_content_stream` + `st.write_stream`) over a single blocking call so the page feels responsive.
- Validate input **before** the API call (empty code is already handled). Consider adding a max character limit if you expect very large pastes.
- If you add file upload, still send a bounded excerpt to the model. Do not silently upload whole projects.
- Handle API failures in the UI (already done with `try/except`). Avoid leaking the raw key in error text.
- When adding languages, update both the `selectbox` options and any docs that list them.

## Security notes

- The snippet you paste is sent to Google’s Gemini API. Assume it leaves your machine.
- The API key in `.streamlit/secrets.toml` can spend quota. Rotate it if it leaks.
- This reviewer flags *obvious* security issues when they are visible in the snippet. It is not a SAST tool, dependency scanner, or substitute for threat modeling.

## Tech stack

| Piece | Choice |
|-------|--------|
| UI | [Streamlit](https://streamlit.io/) |
| Model API | [Google Gen AI SDK](https://github.com/googleapis/python-genai) (`google-genai`) |
| Model | `gemini-3.5-flash-lite` |

## License

Personal project. Add a license file if you publish or share the repository.
