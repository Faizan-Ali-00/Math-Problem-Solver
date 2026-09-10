import os
import re
import base64
from dotenv import load_dotenv
from groq import Groq


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"


def clean_response(text):
    """
    Remove any leaked <think>...</think> reasoning blocks, and normalize
    any bracket-style LaTeX the model slips into $ / $$ so Streamlit can
    actually render it as math.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Convert \[ ... \] (display math) to $$ ... $$
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    # Convert [ ... ] used as display math (common model slip) to $$ ... $$
    # Only when it looks mathy (contains a backslash command or ^ or _ or =)
    text = re.sub(r"(?<!\$)\[\s*((?:[^\[\]]*[\\=^_][^\[\]]*))\]", r"$$\1$$", text)
    # Convert \( ... \) (inline math) to $ ... $
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text)

    return text


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

- Circle (given center and radius, or derivable from the answer): DIAGRAM: PLOTCIRCLE: <center_x>,<center_y>,<radius>
  e.g. DIAGRAM: PLOTCIRCLE: 4,7,4.47

- Circle with a tangent line from an external point: DIAGRAM: PLOTTANGENT: <center_x>,<center_y>,<radius>,<point_x>,<point_y>
  e.g. DIAGRAM: PLOTTANGENT: 2,-1,5,8,4

- Semicircle (half circle with its diameter, e.g. from a construction problem): DIAGRAM: PLOTSEMICIRCLE: <center_x>,<center_y>,<radius>,<orientation>
  orientation is one of: upper, lower, left, right
  e.g. DIAGRAM: PLOTSEMICIRCLE: 2,3,5,upper

- Any other curve/relation in x and y (ellipse, parabola, hyperbola, or any implicit equation):
  DIAGRAM: PLOTIMPLICIT: <expression in x and y that equals zero>
  e.g. DIAGRAM: PLOTIMPLICIT: (x-4)**2 + (y-7)**2 - 20

- Any polygon (triangle from 3 points, quadrilateral, etc.) given by vertex coordinates:
  DIAGRAM: PLOTSHAPE: x1,y1;x2,y2;x3,y3;...
  e.g. DIAGRAM: PLOTSHAPE: 2,3;8,5;6,11

- A triangle inscribed in a circle (i.e. its circumscribed circle) — give ONLY the
  triangle's 3 vertices, the circle is computed automatically:
  DIAGRAM: PLOTINSCRIBED: x1,y1;x2,y2;x3,y3
  e.g. DIAGRAM: PLOTINSCRIBED: 0,0;4,0;2,5

- If no diagram would help (e.g. a pure numeric calculation): DIAGRAM: NONE

If radius is a surd like 2√5, convert it to a decimal approximation for the diagram line (e.g. 4.47).
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800,
        reasoning_effort="low",
        include_reasoning=False
    )
    return clean_response(response.choices[0].message.content)


def explain_definition(term, level="Matric"):
    prompt = f"""
You are a friendly math tutor for a {level}-level student in Pakistan.

Explain the concept: "{term}"

IMPORTANT FORMAT RULES:
- Do NOT show internal thinking, reasoning tags, or any <think> content. Only output the final formatted answer.
- Write ALL math using LaTeX notation with $ signs, e.g. write $x^2$
  NOT x**2
- Use $$ ... $$ for equations on their own line, and $ ... $ for inline math.
- NEVER use \[ ... \], [ ... ], \( ... \), or bare ( ... ) as math delimiters. Only $ and $$ are valid.
- Do not insert stray commas or spacing commands like \, or \; inside coordinate pairs — write (-3, 3) as $(-3, 3)$ cleanly.

CRITICAL ACCURACY RULE FOR CIRCLES AND TANGENTS:
- Before using "radius is perpendicular to the tangent at a point," you MUST first
  confirm that point actually lies ON the circle by checking distance from center = radius.
- If a given point is OUTSIDE the circle (distance from center > radius), it is NOT the
  point of tangency, and you must NOT assume the line from the center to that external
  point is perpendicular to the tangent — that shortcut is invalid for external points.
- For a tangent from an external point P to a circle with center C and radius r:
  1. Compute d = distance from C to P. If d < r, no tangent exists (P is inside).
     If d = r, P is the tangency point itself, and the tangent is perpendicular to CP at P.
  2. If d > r, there are generally TWO tangent lines. Find them either by:
     (a) finding the actual tangency point(s) T where CT ⟂ TP and |CT| = r, or
     (b) setting up a line through P with unknown slope m, then requiring the
         perpendicular distance from C to that line equals r, and solving for m.
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
(One line only, choose exactly ONE of these formats — pick whichever fits best:

- Function graph (y = f(x)): PLOTFUNC: <expression in x>
  e.g. PLOTFUNC: x**2 - 4

- Right triangle: PLOTTRIANGLE: <leg_a>,<leg_b>
  e.g. PLOTTRIANGLE: 3,4

- Circle: PLOTCIRCLE: <center_x>,<center_y>,<radius>
  e.g. PLOTCIRCLE: 2,3,5

- Circle with a tangent line from an external point: PLOTTANGENT: <center_x>,<center_y>,<radius>,<point_x>,<point_y>
  e.g. PLOTTANGENT: 2,-1,5,8,4

- Semicircle (half circle with its diameter): PLOTSEMICIRCLE: <center_x>,<center_y>,<radius>,<orientation>
  orientation is one of: upper, lower, left, right
  e.g. PLOTSEMICIRCLE: 2,3,5,upper

- Any other curve/relation in x and y — ellipse, parabola, hyperbola, or
  any implicit equation (write the expression that equals zero on the curve):
  PLOTIMPLICIT: <expression in x and y>
  e.g. PLOTIMPLICIT: x**2/16 + y**2/9 - 1

- Any polygon (square, rectangle, quadrilateral, general triangle, pentagon,
  etc.) — give its vertices as coordinate pairs separated by semicolons:
  PLOTSHAPE: x1,y1;x2,y2;x3,y3;...
  e.g. PLOTSHAPE: 0,0;4,0;4,3;0,3

- A triangle inscribed in a circle (its circumscribed circle) — give ONLY the
  triangle's 3 vertices, the circle is computed automatically:
  PLOTINSCRIBED: x1,y1;x2,y2;x3,y3
  e.g. PLOTINSCRIBED: 0,0;4,0;2,5

- If this concept truly cannot be visualized (e.g. a pure number property,
  an algebraic identity with no geometric picture): NONE

If the topic involves BOTH a circle and a tangent/external point, prefer PLOTTANGENT over PLOTCIRCLE so the diagram shows the full picture.)

Keep language appropriate for {level} level.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
        reasoning_effort="low",
        include_reasoning=False
    )
    return clean_response(response.choices[0].message.content)


def solve_from_image(image_bytes, level="Matric"):
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""
You are a math tutor for a {level}-level student in Pakistan.

Look at the math question in this image. Then solve it.

IMPORTANT FORMAT RULES:
- Do NOT show internal thinking, reasoning tags, or any <think> content. Only output the final formatted answer.
- Write ALL math using LaTeX notation with $ signs, e.g. write $x^2 + 5x + 6 = 0$
  NOT x**2 + 5x + 6 = 0
- Use $$ ... $$ for equations on their own line, and $ ... $ for inline math.
- NEVER use \[ ... \], [ ... ], \( ... \), or bare ( ... ) as math delimiters. Only $ and $$ are valid.
- Do not insert stray commas or spacing commands like \, or \; inside coordinate pairs — write (-3, 3) as $(-3, 3)$ cleanly.

If the image is unclear or not a math question, say so honestly instead of guessing.

Structure your answer as:
**Question Read:** (the equation you see, in LaTeX)

**Solution:**
1. (step one)
2. (step two)
...

**Final Answer:** (in LaTeX)
"""

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                    }
                ]
            }
        ],
        temperature=0.2,
        max_tokens=1000,
        reasoning_effort="none"
    )
    return clean_response(response.choices[0].message.content)