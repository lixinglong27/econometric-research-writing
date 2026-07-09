from docx.oxml import OxmlElement


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "Delta": "Δ",
    "Gamma": "Γ",
    "Lambda": "Λ",
    "Omega": "Ω",
    "Phi": "Φ",
    "Pi": "Π",
    "Psi": "Ψ",
    "Sigma": "Σ",
    "Theta": "Θ",
    "Xi": "Ξ",
}


def _m(tag):
    return OxmlElement(f"m:{tag}")


def normalize_formula_token(text):
    return GREEK.get(text, text)


def _text_run(text):
    run = _m("r")
    text_el = _m("t")
    text_el.text = normalize_formula_token(text)
    run.append(text_el)
    return run


def _script_node(base, sub=None, sup=None):
    if sub is not None and sup is not None:
        node = _m("sSubSup")
        base_tag, sub_tag, sup_tag = _m("e"), _m("sub"), _m("sup")
        base_tag.append(_text_run(base))
        sub_tag.append(_text_run(sub))
        sup_tag.append(_text_run(sup))
        node.append(base_tag)
        node.append(sub_tag)
        node.append(sup_tag)
        return node

    if sub is not None:
        node = _m("sSub")
        base_tag, sub_tag = _m("e"), _m("sub")
        base_tag.append(_text_run(base))
        sub_tag.append(_text_run(sub))
        node.append(base_tag)
        node.append(sub_tag)
        return node

    if sup is not None:
        node = _m("sSup")
        base_tag, sup_tag = _m("e"), _m("sup")
        base_tag.append(_text_run(base))
        sup_tag.append(_text_run(sup))
        node.append(base_tag)
        node.append(sup_tag)
        return node

    return _text_run(base)


def _is_name_char(char):
    return char.isalnum() or char in {".", "'"}


def _read_base(text, start):
    if _is_name_char(text[start]):
        end = start + 1
        while end < len(text) and _is_name_char(text[end]):
            end += 1
        return text[start:end], end
    return text[start], start + 1


def _read_script_value(text, start):
    if start >= len(text):
        return "", start

    if text[start] == "{":
        depth = 1
        end = start + 1
        while end < len(text) and depth:
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
            end += 1
        value = text[start + 1 : end - 1] if depth == 0 else text[start + 1 : end]
        return value, end

    if _is_name_char(text[start]):
        end = start + 1
        while end < len(text) and _is_name_char(text[end]):
            end += 1
        return text[start:end], end

    return text[start], start + 1


def _append_formula_text(omath, text):
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            start = index
            while index < len(text) and text[index].isspace():
                index += 1
            omath.append(_text_run(text[start:index]))
            continue

        base, index = _read_base(text, index)
        sub = None
        sup = None
        while index < len(text) and text[index] in {"_", "^"}:
            marker = text[index]
            value, index = _read_script_value(text, index + 1)
            if marker == "_":
                sub = value
            else:
                sup = value
        omath.append(_script_node(base, sub=sub, sup=sup))


def omath_text(text):
    omath = _m("oMath")
    _append_formula_text(omath, text)
    return omath


def omath_para_text(text):
    para = _m("oMathPara")
    para.append(omath_text(text))
    return para


def append_display_equation(document, text):
    paragraph = document.add_paragraph()
    paragraph._p.append(omath_para_text(text))
    return paragraph


def append_inline_equation(paragraph, text):
    paragraph._p.append(omath_text(text))
    return paragraph


def count_omml(document_element):
    return document_element.xml.count("<m:oMath")


def ensure_math_namespace(document):
    document.element.set("{http://www.w3.org/2000/xmlns/}m", MATH_NS)
