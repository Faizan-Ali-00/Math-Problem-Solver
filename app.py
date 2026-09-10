import re
import streamlit as st
from solver import solve_math, normalize_math_input
from explainer import explain_solution, explain_definition, solve_from_image
from diagrams import plot_function, plot_triangle, plot_circle, plot_implicit, plot_shape, plot_tangent, plot_semicircle, plot_inscribed_triangle

st.set_page_config(page_title="Math Helper", page_icon="📐", layout="centered")


def render_diagram_from_hint(text):
    """
    Scans model output for a diagram hint (PLOTFUNC, PLOTTRIANGLE, PLOTCIRCLE,
    PLOTTANGENT, PLOTSEMICIRCLE, PLOTINSCRIBED, PLOTIMPLICIT, PLOTSHAPE, or NONE)
    and renders the matching diagram. Checks the most specific patterns first
    so generic ones don't misfire.
    """
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

# ---------- Styling ----------
st.markdown("""
<style>
.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: 0px;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 25px;
}
.result-box {
    background-color: #1e293b;
    padding: 18px;
    border-radius: 12px;
    border-left: 4px solid #4f46e5;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📐 Math Question Helper</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">For Matric • Intermediate • BS students</div>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    level = st.selectbox("Your level", ["Matric", "Intermediate", "BS"])
    st.markdown("---")
    st.caption("Tip: You can type naturally — x², x^2, or x**2 all work the same.")

# ---------- Mode Tabs ----------
tab1, tab2, tab3 = st.tabs(["🧮 Solve a Problem", "📖 Understand a Definition", "📷 Snap & Solve"])

# ---------- TAB 1: SOLVE ----------
with tab1:
    st.subheader("Enter your equation or expression")
    question = st.text_input(
        "Enter your equation or expression",
        placeholder="e.g. x² - 5x + 6 = 0",
        key="solve_input",
        help="You can type it naturally: x², 2x, x^2 — all work. Example: x² - 5x + 6 = 0",
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
                        explanation = explain_solution(question, result, level)
                    st.subheader("📖 Step-by-Step Explanation")
                    st.write(explanation)

                    if result["type"] != "equation":
                        st.subheader("📊 Graph")
                        fig = plot_function(normalized_question)
                        st.pyplot(fig)
                    else:
                        render_diagram_from_hint(explanation)

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
                explanation = explain_definition(term, level)

            st.markdown('<div class="result-box">', unsafe_allow_html=True)
            st.write(explanation)
            st.markdown('</div>', unsafe_allow_html=True)

            render_diagram_from_hint(explanation)

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
                    result = solve_from_image(image_data, level)
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.write(result)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Couldn't process the image. Try a clearer photo. Error: {e}")

st.markdown("---")
st.caption("Built with Streamlit + Groq API • FaiziTech AI Solutions")