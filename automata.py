"""Small inspectable machines for the fictional bank coursework.

The NFAs consume Boolean evidence tokens, after textual predicates have been
evaluated. They do not claim that dates or complete records are single letters.
"""

import re

_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩يك", "01234567890123456789یک")


def normalize(text):
    """Unify Persian letter/digit forms and whitespace without joining words."""
    if text is None:
        return ""
    return re.sub(
        r"\s+", " ", str(text).translate(_TRANSLATION).replace("\u200c", " ")
    ).strip()


def suffix_dfa(text, trace=False):
    """Track the longest suffix that is a prefix of پور, or a final ی."""
    prefixes = {"q0": "", "q_p": "پ", "q_po": "پو", "q_pur": "پور", "q_y": "ی"}
    state, steps = "q0", []
    for index, char in enumerate(normalize(text)):
        candidate = prefixes[state] + char
        state = next(
            (
                q
                for q in ("q_pur", "q_po", "q_p", "q_y")
                if candidate.endswith(prefixes[q])
            ),
            "q0",
        )
        if trace:
            steps.append({"index": index, "symbol": char, "state": state})
    accepted = state in {"q_pur", "q_y"}
    return {"accepted": accepted, "steps": steps, "state": state} if trace else accepted


def vowel_dfa(text, trace=False):
    """Remember whether a vowel occurred strictly before the current ending."""
    state, steps = "q0", []
    for index, char in enumerate(normalize(text)):
        seen = state != "q0"
        state = (
            "q_accept"
            if seen and char in "زژوه"
            else "q_v"
            if seen or char in "اآوی"
            else "q0"
        )
        if trace:
            steps.append({"index": index, "symbol": char, "state": state})
    accepted = state == "q_accept"
    return {"accepted": accepted, "steps": steps, "state": state} if trace else accepted


def credit_nfa(last_name, birth_year, trace=False):
    """Parallel evidence paths; acceptance takes priority over rejection.

    Separators are ignored for the two specified compound surnames so that Persian
    half-spaces and ordinary spaces have the same spelling semantics.
    """
    name = normalize(last_name).replace(" ", "")
    try:
        year = int(birth_year)
    except (ValueError, TypeError):
        year = -1
    a = name in {"رضایی‌نژاد".replace("\u200c", ""), "محمدیپور"}
    b = name == "احمدی" and 1370 <= year <= 1404
    states = {"q_start", "q_a", "q_b"}  # epsilon closure of the start state
    steps = [{"index": 0, "symbol": "ε", "states": sorted(states)}] if trace else []
    # The record symbol carries the two independently evaluated predicates.
    transitions = {
        "q_a": {"q_accept"} if a else set(),
        "q_b": {"q_reject"} if b else set(),
    }
    states = set().union(*(transitions.get(q, set()) for q in states))
    decision = (
        "accept"
        if "q_accept" in states
        else "reject"
        if "q_reject" in states
        else "review"
    )
    if trace:
        steps.append(
            {"index": 1, "symbol": f"A={int(a)}, B={int(b)}", "states": sorted(states)}
        )
        return {"accepted": decision == "accept", "decision": decision, "steps": steps}
    return decision == "accept"


def risk_nfa(first, last, year, province, trace=False):
    """Nondeterministically choose two satisfied predicates among three."""
    first, last, province = map(normalize, (first, last, province))
    try:
        year = int(year)
    except (ValueError, TypeError):
        year = -1
    evidence = [
        any(s in last for s in ("اصغری", "جعفری")) and 1360 <= year <= 1380,
        province in {"سیستان و بلوچستان", "هرمزگان", "خوزستان"},
        any(c in first for c in "زن"),
    ]
    states, steps = {"q0"}, []
    for index, bit in enumerate(evidence):
        # Every path can ignore a token, or consume a true token toward its pair.
        states |= ({"q1"} if bit and "q0" in states else set()) | (
            {"q2"} if bit and "q1" in states else set()
        )
        if trace:
            steps.append(
                {
                    "index": index,
                    "symbol": f"{'ABC'[index]}={int(bit)}",
                    "states": sorted(states),
                }
            )
    accepted = "q2" in states
    return (
        {"accepted": accepted, "steps": steps, "evidence": evidence}
        if trace
        else accepted
    )


def balance_tm(balance, threshold=100_000_000_000, trace=False):
    """A bounded tape-machine simulation: read digits, compare, write, halt.

    The comparison register is pedagogical (a multi-tape/register machine), rather
    than a claim to enumerate a minimal single-tape transition table. Numeric input
    is retained by the pipeline separately from this machine's output tape.
    """
    if isinstance(balance, bool) or not isinstance(balance, int) or balance < 0:
        raise ValueError("Balance must be a nonnegative integer number of IRR.")
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 0:
        raise ValueError("Threshold must be a nonnegative integer.")
    tape, head, register, steps = list(str(balance)) + ["□"], 0, 0, []
    while tape[head] != "□":
        register = register * 10 + int(tape[head])
        if trace:
            steps.append(
                {"index": head, "symbol": tape[head], "state": "q_read", "head": head}
            )
        head += 1
    blocked = register > threshold
    if trace:
        steps.append({"index": head, "symbol": "□", "state": "q_compare", "head": head})
    value = "مسدود" if blocked else balance
    if blocked:
        tape = list(value) + ["□"]
    if trace:
        steps.append(
            {
                "index": head + 1,
                "symbol": str(value),
                "state": "q_block" if blocked else "q_accept",
                "head": 0,
            }
        )
        return {
            "accepted": not blocked,
            "blocked": blocked,
            "value": value,
            "steps": steps,
            "tape": "".join(tape),
        }
    return value


def automaton_spec(kind):
    """Diagram edges use character classes or named record predicates."""
    specs = {
        "suffix": (
            ["q0", "q_p", "q_po", "q_pur", "q_y"],
            "q0",
            ["q_pur", "q_y"],
            [("q0", "پ", "q_p"), ("q_p", "و", "q_po"), ("q_po", "ر", "q_pur")]
            + [(q, "ی", "q_y") for q in ["q0", "q_p", "q_po", "q_pur", "q_y"]]
            + [(q, "پ", "q_p") for q in ["q_p", "q_po", "q_pur", "q_y"]]
            + [(q, "otherwise", "q0") for q in ["q0", "q_p", "q_po", "q_pur", "q_y"]],
            "DFA: accept only a final ی or پور. یی is already included by final ی. Explicit character edges take precedence over otherwise.",
        ),
        "vowel": (
            ["q0", "q_v", "q_accept"],
            "q0",
            ["q_accept"],
            [("q0", "اآوی", "q_v"), ("q0", "other", "q0")]
            + [(q, "زژوه", "q_accept") for q in ["q_v", "q_accept"]]
            + [(q, "other", "q_v") for q in ["q_v", "q_accept"]],
            "DFA: a vowel must occur before the final ز، ژ، و، ه. A single و is rejected.",
        ),
        "credit": (
            ["q_start", "q_a", "q_b", "q_accept", "q_reject"],
            "q_start",
            ["q_accept"],
            [
                ("q_start", "ε", "q_a"),
                ("q_start", "ε", "q_b"),
                ("q_a", "A: specified priority surname", "q_accept"),
                ("q_b", "B: احمدی and 1370–1404", "q_reject"),
            ],
            "NFA over record predicates: A accepts, B rejects, no matching path means review. Compound surname separators are normalized.",
        ),
        "risk": (
            ["q0", "q1", "q2"],
            "q0",
            ["q2"],
            [(q, "0 or 1 (ignore)", q) for q in ["q0", "q1", "q2"]]
            + [("q0", "1 (choose)", "q1"), ("q1", "1 (choose)", "q2")],
            "NFA reads A, B, C evidence bits and accepts at least two true bits. Subset construction yields a DFA of reachable state sets; worst-case exponential growth is a general bound, not a measurement of this small example.",
        ),
        "balance": (
            ["q_read", "q_compare", "q_block", "q_accept"],
            "q_read",
            ["q_accept"],
            [
                ("q_read", "digit: accumulate, move right", "q_read"),
                ("q_read", "blank", "q_compare"),
                ("q_compare", "> threshold: write مسدود, halt", "q_block"),
                ("q_compare", "≤ threshold: halt", "q_accept"),
            ],
            "Educational tape/register machine: scan decimal digits, compare the accumulated register, and write a blocked marker. This is not a minimal single-tape transition table.",
        ),
    }
    if kind not in specs:
        raise ValueError(f"Unknown machine: {kind}")
    states, start, accepting, transitions, description = specs[kind]
    return dict(
        states=states,
        start=start,
        accepting=accepting,
        transitions=transitions,
        description=description,
    )
