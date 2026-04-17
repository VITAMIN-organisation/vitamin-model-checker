import re


def ltl_to_ctl(ltl_formula):
    """Lightweight string rewrite from LTL notation to a CTL-shaped form.

    Not semantics-preserving: this only adds universal path quantifiers before
    temporal operators and wraps bare U occurrences so downstream components
    that expect an A-prefixed shape can accept the string.
    """
    # Prefix X/F/G with A when not already prefixed by A or E
    ltl_formula = re.sub(r"(?<![AE])([XFG])", r"A\1", ltl_formula)

    # Wrap bare U occurrences with A(...) on both sides; tolerate simple atoms or parens
    until_pattern = (
        r"(\([^()]*\)|A\([^()]*\)|[a-zA-Z]\w*)\s*U\s*"
        r"(\([^()]*\)|A\([^()]*\)|[a-zA-Z]\w*)"
    )
    placeholder = "__U_PLACEHOLDER__"
    while placeholder in ltl_formula:
        placeholder = f"{placeholder}_X"

    # Iterate until no raw U matches remain
    while True:
        new_formula = re.sub(until_pattern, rf"A(\1{placeholder}\2)", ltl_formula)
        if new_formula == ltl_formula:
            break
        ltl_formula = new_formula

    return ltl_formula.replace(placeholder, "U")
