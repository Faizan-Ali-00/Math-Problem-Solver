import numpy as np
import matplotlib.pyplot as plt
import sympy as sp


def _dark_style(fig, ax):
    """Apply dark theme styling to a matplotlib figure/axes."""
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    ax.tick_params(colors='white')
    ax.title.set_color('white')
    for spine in ax.spines.values():
        spine.set_color('white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')


def plot_inscribed_triangle(vertices, labels=("A", "B", "C")):
    """
    Draws a triangle together with its circumscribed circle (the circle
    passing through all three vertices) — i.e. a triangle inscribed in a
    circle. Only the triangle's three vertices are needed; the circle's
    center and radius are computed automatically.
    """
    if len(vertices) != 3:
        raise ValueError("plot_inscribed_triangle requires exactly 3 vertices")

    (Ax, Ay), (Bx, By), (Cx, Cy) = [(float(x), float(y)) for x, y in vertices]

    D = 2 * (Ax * (By - Cy) + Bx * (Cy - Ay) + Cx * (Ay - By))
    if abs(D) < 1e-9:
        raise ValueError("The three points are collinear — no circle passes through them")

    ux = ((Ax**2 + Ay**2) * (By - Cy) + (Bx**2 + By**2) * (Cy - Ay) + (Cx**2 + Cy**2) * (Ay - By)) / D
    uy = ((Ax**2 + Ay**2) * (Cx - Bx) + (Bx**2 + By**2) * (Ax - Cx) + (Cx**2 + Cy**2) * (Bx - Ax)) / D
    r = ((Ax - ux) ** 2 + (Ay - uy) ** 2) ** 0.5

    fig, ax = plt.subplots(figsize=(5.5, 5.5))

    # Circumscribed circle
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(ux + r * np.cos(theta), uy + r * np.sin(theta), color='#4f46e5', linewidth=2)

    # Triangle
    tri_x = [Ax, Bx, Cx, Ax]
    tri_y = [Ay, By, Cy, Ay]
    ax.plot(tri_x, tri_y, color='#f97316', linewidth=2.5, marker='o', markersize=5)

    # Vertex labels
    for (vx, vy), lab in zip([(Ax, Ay), (Bx, By), (Cx, Cy)], labels):
        ax.annotate(lab, (vx, vy), textcoords="offset points", xytext=(8, 8),
                    color='white', fontsize=12, fontweight='bold')

    # Circumcenter
    ax.plot(ux, uy, 'o', color='#22c55e', markersize=5)
    ax.annotate("O", (ux, uy), textcoords="offset points", xytext=(6, -12),
                color='#22c55e', fontsize=10, fontweight='bold')

    ax.set_aspect('equal')
    margin = r * 0.3
    ax.set_xlim(ux - r - margin, ux + r + margin)
    ax.set_ylim(uy - r - margin, uy + r + margin)
    ax.axis('off')
    ax.set_title(f"Triangle {''.join(labels)} inscribed in circle (r ≈ {r:.2f})",
                 fontsize=12, fontweight='bold', color='white')
    _dark_style(fig, ax)
    return fig


def plot_function(expr_str, x_range=(-10, 10)):
    """Draws y = f(x) for a single-variable expression, e.g. 'x**2 - 4'."""
    x = sp.symbols('x')
    expr = sp.sympify(expr_str)
    f = sp.lambdify(x, expr, 'numpy')

    xs = np.linspace(x_range[0], x_range[1], 400)
    try:
        ys = np.asarray(f(xs), dtype=float)
        if ys.shape != xs.shape:
            raise ValueError("Shape mismatch — falling back to scalar eval")
    except Exception:
        ys = np.array([float(f(v)) for v in xs])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, ys, color='#4f46e5', linewidth=2.5)
    ax.axhline(0, color='#94a3b8', linewidth=1)
    ax.axvline(0, color='#94a3b8', linewidth=1)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_title(f"y = {expr_str}", fontsize=13, fontweight='bold')
    _dark_style(fig, ax)
    return fig


def plot_implicit(equation_str, x_range=(-10, 10), y_range=(-10, 10)):
    """
    Draws ANY implicit curve given as an expression in x and y that equals
    zero on the curve. Covers ellipses, parabolas, hyperbolas, and any
    other conic or relation, e.g.:
    - Ellipse:    x**2/16 + y**2/9 - 1
    - Parabola:   y**2 - 4*x
    - Hyperbola:  x**2/9 - y**2/4 - 1
    """
    x, y = sp.symbols('x y')
    expr = sp.sympify(equation_str)
    f = sp.lambdify((x, y), expr, 'numpy')

    xs = np.linspace(x_range[0], x_range[1], 400)
    ys = np.linspace(y_range[0], y_range[1], 400)
    X, Y = np.meshgrid(xs, ys)
    Z = np.asarray(f(X, Y), dtype=float)
    if not np.isfinite(Z).all():
        Z = np.nan_to_num(Z, nan=1e6, posinf=1e6, neginf=-1e6)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contour(X, Y, Z, levels=[0], colors='#4f46e5', linewidths=2.5)
    ax.axhline(0, color='#94a3b8', linewidth=1)
    ax.axvline(0, color='#94a3b8', linewidth=1)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_aspect('equal')
    ax.set_title(f"{equation_str} = 0", fontsize=12, fontweight='bold')
    _dark_style(fig, ax)
    return fig


def plot_shape(vertices, labels=None):
    """
    Draws ANY closed polygon from a list of (x, y) vertex tuples — squares,
    rectangles, quadrilaterals, general triangles, pentagons, etc.
    Labels each vertex and shows each side's length.
    """
    vertices = [(float(vx), float(vy)) for vx, vy in vertices]
    n = len(vertices)
    if labels is None:
        labels = [chr(65 + i) for i in range(n)]  # A, B, C, ...

    closed = vertices + [vertices[0]]
    xs = [p[0] for p in closed]
    ys = [p[1] for p in closed]

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(xs, ys, color='#4f46e5', linewidth=2.5, marker='o', markersize=5)

    for i, (vx, vy) in enumerate(vertices):
        ax.annotate(labels[i], (vx, vy), textcoords="offset points", xytext=(8, 8),
                    color='white', fontsize=12, fontweight='bold')

    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, f"{length:.1f}", color='#e2e8f0', fontsize=9,
                bbox=dict(facecolor='#0e1117', edgecolor='none', pad=1))

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"{''.join(labels)}", fontsize=13, fontweight='bold', color='white')
    _dark_style(fig, ax)
    return fig


def plot_semicircle(h, k, r, orientation="upper"):
    """
    Draws a semicircle: the arc of a circle centered at (h, k) with radius r,
    together with its diameter as a straight base line.
    orientation: 'upper', 'lower', 'left', or 'right' — which half is drawn.
    """
    h, k, r = float(h), float(k), float(r)

    angle_ranges = {
        "upper": (0, np.pi),
        "lower": (np.pi, 2 * np.pi),
        "right": (-np.pi / 2, np.pi / 2),
        "left": (np.pi / 2, 3 * np.pi / 2),
    }
    start, end = angle_ranges.get(orientation, angle_ranges["upper"])
    theta = np.linspace(start, end, 150)
    xs = h + r * np.cos(theta)
    ys = k + r * np.sin(theta)

    # Diameter endpoints are the two ends of this same theta range
    Ax, Ay = h + r * np.cos(start), k + r * np.sin(start)
    Bx, By = h + r * np.cos(end), k + r * np.sin(end)

    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot(xs, ys, color='#4f46e5', linewidth=2.5)
    ax.plot([Ax, Bx], [Ay, By], color='#94a3b8', linewidth=2, linestyle='--')

    ax.plot(h, k, 'o', color='#f97316', markersize=6)
    ax.annotate("C", (h, k), textcoords="offset points", xytext=(-14, 10),
                color='white', fontsize=11, fontweight='bold')
    ax.annotate(f"A ({Ax:g}, {Ay:g})", (Ax, Ay), textcoords="offset points",
                xytext=(-10, -16), color='white', fontsize=10)
    ax.annotate(f"B ({Bx:g}, {By:g})", (Bx, By), textcoords="offset points",
                xytext=(-10, -16), color='white', fontsize=10)

    ax.axhline(0, color='#475569', linewidth=0.8)
    ax.axvline(0, color='#475569', linewidth=0.8)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_aspect('equal')
    ax.set_xlim(h - r * 1.5, h + r * 1.5)
    ax.set_ylim(k - r * 1.5, k + r * 1.5)
    ax.set_title(f"Semicircle: centre ({h:g}, {k:g}), r = {r:g}",
                 fontsize=12, fontweight='bold')
    _dark_style(fig, ax)
    return fig


def plot_circle(h, k, r):
    """Draws a circle centered at (h, k) with radius r."""
    h, k, r = float(h), float(k), float(r)
    theta = np.linspace(0, 2 * np.pi, 200)
    xs = h + r * np.cos(theta)
    ys = k + r * np.sin(theta)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(xs, ys, color='#4f46e5', linewidth=2.5)
    ax.plot(h, k, 'o', color='#f97316', markersize=6)

    # Center label: placed above-left of the dot, using pixel offset so it
    # never collides regardless of circle size
    ax.annotate(f"({h:g}, {k:g})", (h, k), textcoords="offset points", xytext=(-15, 12),
                color='white', fontsize=10, ha='right')

    # Radius line drawn slightly below center so its label has clear space
    radius_y = k - r * 0.35
    ax.plot([h, h + r], [radius_y, radius_y], linestyle='--', color='#94a3b8', linewidth=1.2)
    ax.plot([h, h], [k, radius_y], linestyle=':', color='#475569', linewidth=0.8)
    ax.annotate(f"r = {r:g}", (h + r / 2, radius_y), textcoords="offset points",
                xytext=(0, 8), color='#e2e8f0', fontsize=10, ha='center')

    ax.axhline(0, color='#475569', linewidth=0.8)
    ax.axvline(0, color='#475569', linewidth=0.8)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_aspect('equal')
    ax.set_xlim(h - r * 1.5, h + r * 1.5)
    ax.set_ylim(k - r * 1.5, k + r * 1.5)
    ax.set_title(f"Circle: (x-{h:g})² + (y-{k:g})² = {r:g}²",
                 fontsize=12, fontweight='bold')
    _dark_style(fig, ax)
    return fig


def plot_tangent(h, k, r, px, py):
    """
    Draws a circle centered at (h, k) with radius r, an external point P,
    and the correct tangent line(s) from P to the circle — computed
    geometrically (not trusting any model-generated algebra), so the
    diagram is always accurate.
    """
    h, k, r = float(h), float(k), float(r)
    px, py = float(px), float(py)

    d = ((px - h) ** 2 + (py - k) ** 2) ** 0.5

    fig, ax = plt.subplots(figsize=(6, 6))

    # Draw the circle
    theta = np.linspace(0, 2 * np.pi, 200)
    cx = h + r * np.cos(theta)
    cy = k + r * np.sin(theta)
    ax.plot(cx, cy, color='#4f46e5', linewidth=2.5)
    ax.plot(h, k, 'o', color='#f97316', markersize=6)
    ax.annotate("C", (h, k), textcoords="offset points", xytext=(6, 6),
                color='white', fontsize=11, fontweight='bold')

    # Draw the external point
    ax.plot(px, py, 'o', color='#22c55e', markersize=7)
    ax.annotate("P", (px, py), textcoords="offset points", xytext=(8, 8),
                color='white', fontsize=12, fontweight='bold')

    if d < r - 1e-9:
        ax.set_title("Point is INSIDE the circle — no tangent exists",
                     fontsize=11, color='white')
    else:
        phi = np.arctan2(py - k, px - h)
        if abs(d - r) < 1e-9:
            # P is the point of tangency itself
            tangent_angle = phi + np.pi / 2
            length = max(r, 3)
            x1, y1 = px - length * np.cos(tangent_angle), py - length * np.sin(tangent_angle)
            x2, y2 = px + length * np.cos(tangent_angle), py + length * np.sin(tangent_angle)
            ax.plot([x1, x2], [y1, y2], color='#e11d48', linewidth=2, linestyle='--')
            ax.set_title("Tangent at P (P lies on the circle)",
                         fontsize=12, fontweight='bold', color='white')
        else:
            theta_angle = np.arccos(r / d)
            for sign in (1, -1):
                angle = phi + sign * theta_angle
                tx = h + r * np.cos(angle)
                ty = k + r * np.sin(angle)
                ax.plot(tx, ty, 'o', color='#facc15', markersize=5)
                ax.plot([px, tx], [py, ty], color='#e11d48', linewidth=2)
            ax.set_title("Two tangent lines from external point P",
                         fontsize=12, fontweight='bold', color='white')

    ax.axhline(0, color='#475569', linewidth=0.8)
    ax.axvline(0, color='#475569', linewidth=0.8)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_aspect('equal')
    margin = max(r, d) * 0.4
    ax.set_xlim(min(h - r, px) - margin, max(h + r, px) + margin)
    ax.set_ylim(min(k - r, py) - margin, max(k + r, py) + margin)
    _dark_style(fig, ax)
    return fig


def plot_triangle(a, b, c=None, labels=("A", "B", "C")):
    """
    Draws a right triangle with legs a (horizontal) and b (vertical),
    meeting at a right angle at the origin. c is the hypotenuse length
    (computed automatically if not given).
    """
    a, b = float(a), float(b)
    if c is None:
        c = (a ** 2 + b ** 2) ** 0.5

    Ax, Ay = 0, 0
    Bx, By = a, 0
    Cx, Cy = 0, b

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([Ax, Bx, Cx, Ax], [Ay, By, Cy, Ay], color='#4f46e5', linewidth=2.5)

    marker_size = min(a, b) * 0.12
    ax.plot([Ax, Ax + marker_size, Ax + marker_size, Ax],
            [Ay + marker_size, Ay + marker_size, Ay, Ay],
            color='#94a3b8', linewidth=1.2)

    ax.annotate(labels[0], (Ax, Ay), textcoords="offset points", xytext=(-12, -12),
                color='white', fontsize=12, fontweight='bold')
    ax.annotate(labels[1], (Bx, By), textcoords="offset points", xytext=(8, -12),
                color='white', fontsize=12, fontweight='bold')
    ax.annotate(labels[2], (Cx, Cy), textcoords="offset points", xytext=(-8, 8),
                color='white', fontsize=12, fontweight='bold')

    ax.text(a / 2, -max(a, b) * 0.08, f"{labels[0]}{labels[1]} = {a:g} cm",
            color='#e2e8f0', ha='center', fontsize=10)
    ax.text(-max(a, b) * 0.12, b / 2, f"{labels[0]}{labels[2]} = {b:g} cm",
            color='#e2e8f0', va='center', rotation=90, fontsize=10)
    mx, my = (Bx + Cx) / 2, (By + Cy) / 2
    ax.text(mx + max(a, b) * 0.05, my, f"{labels[1]}{labels[2]} = {c:.2f} cm",
            color='#e2e8f0', fontsize=10)

    ax.set_xlim(-max(a, b) * 0.3, max(a, b) * 1.2)
    ax.set_ylim(-max(a, b) * 0.3, max(a, b) * 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Right Triangle ({labels[0]}{labels[1]}{labels[2]})",
                 fontsize=13, fontweight='bold', color='white')
    _dark_style(fig, ax)
    return fig