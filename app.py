import streamlit as st
from google import genai
from prompt import SYSTEM_PROMPT


st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🤖",
    layout="wide",
)

MODEL = "gemini-3.5-flash-lite"

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


st.title("🤖 AI Code Reviewer")

with st.sidebar:

    st.header("⚙️ Review Settings")

    st.markdown(
        """
        This AI reviewer analyzes code for:

        - 📖 Readability
        - 🏗️ Structure
        - 🔧 Maintainability
        """
    )

    st.divider()

    st.caption("Powered by Google Gemini")


st.markdown(
    """
Review your code for readability, structure, maintainability,
correctness, and security before sending it to a human reviewer.
"""
)

st.divider()

language = st.selectbox(
    "Programming Language",
    [
        "Python",
        "JavaScript",
        "TypeScript",
        "Java",
        "C++",
        "C#",
        "Go",
        "Rust",
        "PHP",
        "SQL",
    ],
)

code = st.text_area(
    "Paste your code",
    height=400,
    placeholder="""def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total
""",
)

review_button = st.button(
    "Review Code",
    type="primary",
    use_container_width=True,
)


def review_code(code: str, language: str):
    prompt = f"""
{SYSTEM_PROMPT}

Programming language:
{language}

Code to review:

```{language.lower()}
{code}
```

Review this code now.
"""

    stream = client.models.generate_content_stream(
        model=MODEL,
        contents=prompt,
    )

    for chunk in stream:
        if chunk.text:
            yield chunk.text


if review_button:
    if not code.strip():
        st.error("Please paste your code first.")
    else:
        st.subheader("📝 AI Review")

        try:
            response = st.write_stream(review_code(code, language))
        except Exception as e:
            st.error("Something went wrong while reviewing the code.")
            st.exception(e)
