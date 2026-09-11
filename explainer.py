import os
import re
import base64
from dotenv import load_dotenv

load_dotenv()

# =========================
# API KEYS
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st_secrets("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st_secrets("GEMINI_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY") or st_secrets("CEREBRAS_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or st_secrets("OPENROUTER_API_KEY")


def st_secrets(name, default=None):
    """Read from Streamlit secrets if available."""
    try:
        import streamlit as st
        return st.secrets[name]
    except Exception:
        return default


# =========================
# MODELS (matching your original)
# =========================

MODEL = "openai/gpt-oss-120b"           # Groq text model
VISION_MODEL = "qwen/qwen3.6-27b"       # Groq vision model


# =========================
# CLEAN RESPONSE
# =========================

def clean_response(text):
    """
    Remove any leaked <think>...</think> reasoning blocks, and normalize
    any bracket-style LaTeX the model slips into $ / $$ so Streamlit can
    actually render it as math.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Convert \[ ... \] (display math) to $$ ... $$
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    # Convert [ ... ] used as display math to $$ ... $$
    text = re.sub(r"(?<!\$)\[\s*((?:[^\[\]]*[\\=^_][^\[\]]*))\]", r"$$\1$$", text)
    # Convert \( ... \) (inline math) to $ ... $
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text)

    return text


# =========================
# PROVIDERS
# =========================

def _call_groq_text(prompt, temperature, max_tokens):
    """Groq text completion with reasoning_effort."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort="low",
        include_reasoning=False,
    )
    return response.choices[0].message.content


def _call_groq_vision(prompt, image_bytes, temperature, max_tokens):
    """Groq vision completion with Qwen 3.6."""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                    },
                ],
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort="none",
    )
    return response.choices[0].message.content


def _call_gemini_text(prompt, temperature, max_tokens):
    """Gemini 2.5 Flash — text fallback."""
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def _call_gemini_vision(prompt, image_bytes, temperature, max_tokens):
    """Gemini 2.5 Flash — vision fallback."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        ],
    )
    return response.text


def _call_cerebras_text(prompt, temperature, max_tokens):
    """Cerebras — fast text fallback."""
    from cerebras.cloud.sdk import Cerebras
    client = Cerebras(api_key=CEREBRAS_API_KEY)
    response = client.chat.completions.create(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _call_openrouter_text(prompt, temperature, max_tokens):
    """OpenRouter — free model fallback."""
    import requests
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_openrouter_vision(prompt, image_bytes, temperature, max_tokens):
    """OpenRouter Qwen VL — vision fallback."""
    import requests
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "qwen/qwen-2.5-vl-7b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                        },
                    ],
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# =========================
# FALLBACK SYSTEM
# =========================

def call_with_fallback(prompt, temperature, max_tokens, image_bytes=None):
    """Call providers in order. Returns (answer, provider_name)."""
    if image_bytes is None:
        providers = []
        if GROQ_API_KEY:
            providers.append(("Groq", lambda: _call_groq_text(prompt, temperature, max_tokens)))
        if GEMINI_API_KEY:
            providers.append(("Gemini", lambda: _call_gemini_text(prompt, temperature, max_tokens)))
        if CEREBRAS_API_KEY:
            providers.append(("Cerebras", lambda: _call_cerebras_text(prompt, temperature, max_tokens)))
        if OPENROUTER_API_KEY:
            providers.append(("OpenRouter", lambda: _call_openrouter_text(prompt, temperature, max_tokens)))
    else:
        providers = []
        if GROQ_API_KEY:
            providers.append(("Groq Vision", lambda: _call_groq_vision(prompt, image_bytes, temperature, max_tokens)))
        if GEMINI_API_KEY:
            providers.append(("Gemini Vision", lambda: _call_gemini_vision(prompt, image_bytes, temperature, max_tokens)))
        if OPENROUTER_API_KEY:
            providers.append(("OpenRouter Qwen-VL", lambda: _call_openrouter_vision(prompt, image_bytes, temperature, max_tokens)))

    if not providers:
        raise Exception("No AI providers configured. Add at least one API key.")

    last_error = None
    for name, func in providers:
        try:
            result = func()
            if result and result.strip():
                return result, name
        except Exception as e:
            last_error = f"{name}: {e}"
            continue

    raise Exception(f"All providers failed. Last error: {last_error}")


# =========================
# EXPLAIN SOLUTION
# =========================

def explain_solution(question, computed_result, level="Matric"):
    prompt = f"""
You are a friendly, patient math tutor for a {level}-level student in Pakistan.

Question: {question}
Verified computed result: {computed_result}

IMPORTANT FORMAT RULES:
- Do NOT show internal thinking, reasoning tags, or any <think> content. Only output the final formatted answer.
- Write ALL math using LaTeX notation with $ signs, e.g. write $x^2 + 5x + 6 = 0$
  NOT x**2 + 5x + 6 = 0
- Use $$ ... $$ for equations on their own line, and $ ... $ for inline math.
- NEVER use \[ ... \], [ ... ], \( ... \), or bare ( ... ) as math delimiters. Only $ and $$ are valid.
- Do not insert stray commas or spacing commands like \, or \; inside coordinate pairs — write (-3, 3) as $(-3, 3)$ cleanly.

Explain step-by-step how to reach this result. Use simple language for
{level} level, break it into clearly numbered steps, and end with a
"**Final Answer:**" line.

CRITICAL ACCURACY RULE FOR CIRCLES AND TANGENTS:
- Before using "radius is perpendicular to the tangent at a point," you MUST first
  confirm that point actually lies ON the circle by checking distance from center = radius.
- If a given point is OUTSIDE the circle, do NOT assume the line from the center to that
  point is perpendicular to the tangent — that shortcut only applies to points on the circle.
- ALWAYS verify any final line/circle equation by checking it against the given conditions
  before presenting it as the answer.

Then add one final line, exactly in this format, choosing whichever ONE fits best:

- Function graph (y = f(x)): DIAGRAM: PLOTFUNC: <expression in x, rearranged to equal zero>
  e.g. DIAGRAM: PLOTFUNC: x**2 - 5*x + 6

- Right triangle: DIAGRAM: PLOTTRIANGLE: <leg_a>,<leg_b>
  e.g. DIAGRAM: PLOTTRIANGLE: 3,4

- Circle: DIAGRAM: PLOTCIRCLE: <center_x>,<center_y>,<radius>
  e.g. DIAGRAM: PLOTCIRCLE: 4,7,4.47

- Circle with a tangent line from an external point: DIAGRAM: PLOTTANGENT: <center_x>,<center_y>,<radius>,<point_x>,<point_y>
  e.g. DIAGRAM: PLOTTANGENT: 2,-1,5,8,4

- Semicircle: DIAGRAM: PLOTSEMICIRCLE: <center_x>,<center_y>,<radius>,<orientation>
  orientation is one of: upper, lower, left, right

- Any other curve/relation: DIAGRAM: PLOTIMPLICIT: <expression in x and y that equals zero>

- Any polygon: DIAGRAM: PLOTSHAPE: x1,y1;x2,y2;x3,y3;...

- A triangle inscribed in a circle: DIAGRAM: PLOTINSCRIBED: x1,y1;x2,y2;x3,y3

- If no diagram would help: DIAGRAM: NONE

If radius is a surd like 2√5, convert it to a decimal approximation for the diagram line (e.g. 4.47).
"""
    try:
        answer, provider = call_with_fallback(prompt, temperature=0.2, max_tokens=800)
        return clean_response(answer), provider
    except Exception as e:
        return f"Could not generate explanation: {e}", "None"


# =========================
# EXPLAIN DEFINITION
# =========================

def explain_definition(term, level="Matric"):
    prompt = f"""
You are a friendly math tutor for a {level}-level student in Pakistan.

Explain the concept: "{term}"

IMPORTANT FORMAT RULES:
- Do NOT show internal thinking, reasoning tags, or any <think> content. Only output the final formatted answer.
- Write ALL math using LaTeX notation with $ signs, e.g. write $x^2$
- Use $$ ... $$ for equations on their own line, and $ ... $ for inline math.
- NEVER use \[ ... \], [ ... ], \( ... \), or bare ( ... ) as math delimiters. Only $ and $$ are valid.

CRITICAL ACCURACY RULE FOR CIRCLES AND TANGENTS:
- Before using "radius is perpendicular to the tangent at a point," you MUST first
  confirm that point actually lies ON the circle by checking distance from center = radius.
- If a given point is OUTSIDE the circle (distance from center > radius), it is NOT the
  point of tangency, and you must NOT assume the line from the center to that external
  point is perpendicular to the tangent — that shortcut is invalid for external points.
- For a tangent from an external point P to a circle with center C and radius r:
  1. Compute d = distance from C to P. If d < r, no tangent exists (P is inside).
     If d = r, P is the tangency point itself, and the tangent is perpendicular to CP at P.
  2. If d > r, there are generally TWO tangent lines.
  3. ALWAYS verify your final line by checking that the perpendicular distance from
     the center to it equals the radius before presenting it as the answer.

Structure your answer EXACTLY like this with these headers:
### Definition
(1-2 simple lines, no jargon)

### Why It Matters
(1-2 lines on real use / where it appears in exams or life)

### Worked Example
(A full numeric example, step by step, using LaTeX)

### Diagram Hint
(One line only, choose exactly ONE of these formats:
- PLOTFUNC: <expression in x>
- PLOTTRIANGLE: <leg_a>,<leg_b>
- PLOTCIRCLE: <center_x>,<center_y>,<radius>
- PLOTTANGENT: <center_x>,<center_y>,<radius>,<point_x>,<point_y>
- PLOTSEMICIRCLE: <center_x>,<center_y>,<radius>,<orientation>
- PLOTIMPLICIT: <expression in x and y>
- PLOTSHAPE: x1,y1;x2,y2;x3,y3;...
- PLOTINSCRIBED: x1,y1;x2,y2;x3,y3
- NONE)

Keep language appropriate for {level} level.
"""
    try:
        answer, provider = call_with_fallback(prompt, temperature=0.3, max_tokens=1000)
        return clean_response(answer), provider
    except Exception as e:
        return f"Could not generate explanation: {e}", "None"


# =========================
# SOLVE FROM IMAGE
# =========================

def solve_from_image(image_bytes, level="Matric"):
    prompt = f"""
You are a math tutor for a {level}-level student in Pakistan.

Look at the math question in this image. Then solve it.

IMPORTANT FORMAT RULES:
- Do NOT show internal thinking, reasoning tags, or any <think> content. Only output the final formatted answer.
- Write ALL math using LaTeX notation with $ signs, e.g. write $x^2 + 5x + 6 = 0$
- Use $$ ... $$ for equations on their own line, and $ ... $ for inline math.
- NEVER use \[ ... \], [ ... ], \( ... \), or bare ( ... ) as math delimiters. Only $ and $$ are valid.

If the image is unclear or not a math question, say so honestly instead of guessing.

Structure your answer as:
**Question Read:** (the equation you see, in LaTeX)

**Solution:**
1. (step one)
2. (step two)
...

**Final Answer:** (in LaTeX)
"""
    try:
        answer, provider = call_with_fallback(
            prompt,
            temperature=0.2,
            max_tokens=1000,
            image_bytes=image_bytes,
        )
        return clean_response(answer), provider
    except Exception as e:
        return f"Could not process image: {e}", "None"
