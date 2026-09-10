import re
import sympy as sp

x = sp.symbols('x')

SUPERSCRIPT_MAP = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
}


def normalize_math_input(text):
    """
    Converts natural math notation typed/pasted by the student into
    a format SymPy can parse:
    - x²      -> x**2
    - x^2     -> x**2
    - 2x      -> 2*x   (implicit multiplication)
    - ×       -> *
    - ÷       -> /
    """
    # Convert superscript digit sequences (x² -> x**2)
    def replace_superscript(match):
        base = match.group(1)
        digits = ''.join(SUPERSCRIPT_MAP[ch] for ch in match.group(2))
        return f"{base}**{digits}"

    text = re.sub(r'([a-zA-Z0-9\)])([⁰¹²³⁴⁵⁶⁷⁸⁹]+)', replace_superscript, text)

    # Convert caret notation (x^2 -> x**2)
    text = text.replace('^', '**')

    # Convert multiplication/division symbols
    text = text.replace('×', '*').replace('÷', '/')

    # Add implicit multiplication: 2x -> 2*x, 3(x+1) -> 3*(x+1)
    text = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', text)

    return text


def solve_expression(expr_str):
    expr = sp.sympify(expr_str)
    result = {
        "type": "expression",
        "original": str(expr),
        "simplified": str(sp.simplify(expr)),
    }
    try:
        result["derivative"] = str(sp.diff(expr, x))
    except Exception:
        result["derivative"] = "N/A"
    try:
        result["integral"] = str(sp.integrate(expr, x))
    except Exception:
        result["integral"] = "N/A"
    return result


def solve_equation(eq_str):
    lhs, rhs = eq_str.split('=')
    equation = sp.Eq(sp.sympify(lhs), sp.sympify(rhs))
    solutions = sp.solve(equation, x)
    return {
        "type": "equation",
        "equation": eq_str,
        "solutions": [str(s) for s in solutions] if solutions else ["No real solution found"]
    }


def solve_math(input_str):
    input_str = normalize_math_input(input_str.strip())
    if "=" in input_str:
        return solve_equation(input_str)
    return solve_expression(input_str)