"""Local coursework interface; no shared cache stores private records."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import streamlit as st

import automata
from bank_core import Config, execute_pipeline
from demo import demo_csv
from notebook_builder import build_notebook

st.set_page_config(page_title="Bank · Automata Workbench", page_icon="◈", layout="wide")
st.markdown(
    """<style>.stApp{background:#f7f5ef;color:#162b3b}h1,h2,h3{color:#132e41}.block-container{padding-top:3rem;max-width:1400px}[data-testid="stMetric"]{border-top:3px solid #26806b;padding:14px;background:white}.stTabs [data-baseweb="tab-list"]{gap:20px;border-bottom:1px solid #ccd5ce}.stTabs [data-baseweb="tab"]{font-weight:600}.lab-label{font-size:.8rem;letter-spacing:.16em;color:#92602f}@media(max-width:640px){.block-container{padding-top:4.5rem}.stTabs [data-baseweb="tab-list"]{gap:8px}}</style>""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="lab-label">THEORY OF LANGUAGES & MACHINES / COURSEWORK LAB</div>',
    unsafe_allow_html=True,
)
st.title("Bank · Automata Workbench")
st.caption(
    "Twenty questions. One traceable pipeline. Fictional banking data, processed locally."
)
overview, dataset, questions, lab, exports = st.tabs(
    [
        "Overview",
        "Dataset & pipeline",
        "Questions 1–20",
        "Automata lab",
        "Notebook & exports",
    ]
)
with dataset:
    st.header("Choose your working dataset")
    mode = st.radio(
        "Source", ["Synthetic demo", "Upload CSV", "Local CSV path"], horizontal=True
    )
    source = demo_csv() if mode == "Synthetic demo" else None
    if mode == "Upload CSV":
        upload = st.file_uploader("Small CSV file", type=["csv"])
        if upload is not None:
            source = upload.getvalue()
        st.caption("Use a local path for large datasets to avoid buffering an upload.")
    if mode == "Local CSV path":
        path = st.text_input("CSV path on this computer")
        if path:
            source = Path(path).expanduser()
    left, right = st.columns(2)
    birth = left.text_input("Your Shamsi birth date", "1380/01/01")
    relative = right.text_input("Relative’s last name (Q20)")
    city = right.text_input("Relative’s city (Q20)")
    with st.expander("Processing settings"):
        chunk = st.number_input("Rows per chunk", 100, 1000000, 10000, 100)
        seed = st.number_input("Random seed", 0, 2147483647, 42)
        year = st.number_input("Reference Shamsi year", 1300, 1600, 1405)
    config = Config(
        seed=int(seed),
        reference_year=int(year),
        birth_date=birth,
        relative_last_name=relative,
        relative_city=city,
    )

    def fingerprint():
        if isinstance(source, Path):
            stat = source.stat()
            identity = f"{source.resolve()}:{stat.st_size}:{stat.st_mtime_ns}"
        else:
            identity = hashlib.sha256(source or b"").hexdigest()
        return hashlib.sha256((identity + repr(asdict(config))).encode()).hexdigest()

    try:
        current = fingerprint() if source is not None else None
    except OSError:
        current = None
    if st.button("Run all 20 questions", type="primary", disabled=source is None):
        try:
            with st.spinner("Reading chunks and evaluating coursework rules…"):
                status = st.empty()

                def progress(event):
                    status.caption(
                        f"Pass {event['pass']} of 2 \u00b7 {event['rows']:,} rows processed"
                    )

                candidate = execute_pipeline(
                    source, chunksize=int(chunk), config=config, progress=progress
                )
            st.session_state.report = candidate
            st.session_state.signature = fingerprint()
            st.success("Complete. Explore the questions and export your notebook.")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            st.error(f"Could not process this input: {exc}")
    st.caption(
        "Use Streamlit’s Stop control to interrupt a run. Invalid input preserves your previous successful result."
    )
report = st.session_state.get("report")
fresh = report is not None and current == st.session_state.get("signature")
if report is not None and not fresh:
    st.warning(
        "Inputs changed. Previous results are preserved; run again to update them."
    )
with overview:
    st.header("From raw records to explainable decisions")
    st.write(
        "Start with the synthetic demo, inspect each question, then test names and balances in the automata lab. Your source CSV is read only."
    )
    a, b, c = st.columns(3)
    a.metric("Coursework questions", "20")
    b.metric("Memory strategy", "Chunked")
    c.metric("Private Q20 previews", "Hidden")
    st.subheader("A reproducible workflow")
    st.write(
        "1. Choose a dataset and personal criteria.\n\n2. Run the pipeline and inspect counts, explanations, and bounded examples.\n\n3. Export your notebook. Keep relative records private."
    )
    if report is not None:
        st.subheader("Latest pipeline statistics")
        metrics = st.columns(3)
        for column, key, label in zip(
            metrics,
            ["rows", "passes", "invalid_national_ids"],
            ["Rows processed", "Pipeline passes", "Invalid IDs preserved"],
        ):
            column.metric(label, f"{report.stats.get(key, 0):,}")
        st.caption(
            f"Chunk size: {report.stats.get('chunksize', 0):,} rows. Monetary values remain integer IRR."
        )
with questions:
    st.header("Explore the assignment")
    if report is None:
        st.info(
            "Run the synthetic demo in Dataset & pipeline to populate all twenty questions."
        )
    else:
        number = st.selectbox(
            "Question",
            list(range(1, 21)),
            format_func=lambda n: f"Q{n:02d} · {report.questions[n].get('title', '')}",
        )
        result = report.questions[number]
        st.subheader(result.get("title", f"Question {number}"))
        st.metric("Matching / processed records", result.get("count", 0))
        summary = result.get("summary", {})
        if number == 9 and summary:
            chart = pd.DataFrame(
                [
                    {"Cohort": k, "Average age": v["average_age"], "Count": v["count"]}
                    for k, v in summary.items()
                ]
            ).set_index("Cohort")
            st.bar_chart(chart[["Average age"]])
            st.dataframe(chart, width="stretch")
        elif summary:
            for key, value in summary.items():
                st.write(f"**{key.replace('_', ' ').capitalize()}**: {value}")
        if number == 20:
            st.info(
                "Relative records are private. No preview or notebook row output is shown. Use the explicit local export."
            )
        elif result.get("preview"):
            preview = pd.DataFrame(result["preview"])
            if "tm_balance" in preview:
                preview["tm_balance"] = preview["tm_balance"].astype(str)
            st.dataframe(preview, width="stretch", hide_index=True)
        else:
            st.caption("No example rows for this question.")
with lab:
    st.header("Follow the machine, step by step")
    kind = st.selectbox(
        "Machine",
        ["suffix", "vowel", "credit", "risk", "balance"],
        format_func=lambda k: {
            "suffix": "Suffix DFA",
            "vowel": "Vowel DFA",
            "credit": "Credit NFA",
            "risk": "Risk NFA",
            "balance": "Balance TM",
        }[k],
    )
    spec = automata.automaton_spec(kind)
    dot = [
        'digraph G { rankdir=LR; bgcolor="transparent"; node [shape=circle,color="#146b58"];'
    ]
    dot.append("entry [shape=point];")
    dot.append(f"entry -> {json.dumps(spec['start'])};")
    for state in spec["states"]:
        dot.append(
            f"{json.dumps(state)} [shape={'doublecircle' if state in spec['accepting'] else 'circle'}];"
        )
    for start, label, end in spec["transitions"]:
        dot.append(
            f"{json.dumps(start)} -> {json.dumps(end)} [label={json.dumps(label, ensure_ascii=False)}];"
        )
    st.graphviz_chart("\n".join(dot + ["}"]))
    st.write(spec["description"])
    name = st.text_input("Name / last name", "محمدیپور") if kind != "balance" else ""
    first = (
        st.text_input("First name for risk machine", "محمد") if kind == "risk" else ""
    )
    machine_year = (
        st.number_input("Birth year", 1200, 1600, 1380)
        if kind in {"credit", "risk"}
        else 1380
    )
    province = st.text_input("Province", "تهران") if kind == "risk" else ""
    balance = (
        st.number_input("Balance (IRR)", 0, 1000000000000000, 1000)
        if kind == "balance"
        else 0
    )
    trace_signature = (kind, name, first, int(machine_year), province, int(balance))
    if st.button("Trace machine"):
        if kind == "suffix":
            trace = automata.suffix_dfa(name, trace=True)
        elif kind == "vowel":
            trace = automata.vowel_dfa(name, trace=True)
        elif kind == "credit":
            trace = automata.credit_nfa(name, int(machine_year), trace=True)
        elif kind == "risk":
            trace = automata.risk_nfa(
                first, name, int(machine_year), province, trace=True
            )
        else:
            trace = automata.balance_tm(int(balance), trace=True)
        st.session_state.machine_trace = trace
        st.session_state.machine_signature = trace_signature
    if st.session_state.get("machine_signature") == trace_signature:
        trace = st.session_state.machine_trace
        decision = trace.get(
            "decision", "accepted" if trace.get("accepted") else "rejected"
        )
        st.subheader(f"Result: {decision.capitalize()}")
        if "value" in trace:
            st.write(f"Output: {trace['value']}")
        steps = trace["steps"]
        selected = (
            st.slider("Trace step", 0, len(steps) - 1, 0, key="trace_step")
            if len(steps) > 1
            else 0
        )
        step = steps[selected]
        current_state = step.get("state", ", ".join(step.get("states", [])))
        a, b, c = st.columns(3)
        a.metric("Current state(s)", current_state)
        b.metric("Read symbol", str(step.get("symbol", "")))
        c.metric("Tape head / step", str(step.get("head", selected)))
        st.caption(
            f"Step {selected + 1} of {len(steps)}. Move the slider to follow the computation."
        )
        with st.expander("All transition steps"):
            st.dataframe(steps, width="stretch", hide_index=True)
        with st.expander("Raw machine trace"):
            st.json(trace)
with exports:
    st.header("Keep the work reproducible")
    st.write(
        "Notebooks contain coursework logic and summaries; Q20 rows remain hidden. Treat exports from your own dataset as private."
    )
    if report is None:
        st.info("Process a dataset before exporting.")
    else:
        st.download_button(
            "Download coursework notebook",
            build_notebook(report, source_label=mode),
            "bank_coursework.ipynb",
            "application/x-ipynb+json",
            disabled=not fresh,
        )
        st.subheader("Private relative records · Q20")
        st.caption(
            "Re-reads the source in chunks. Choose a new private destination outside this repository."
        )
        destination = st.text_input("Private destination CSV path")
        if st.button("Export private Q20 CSV", disabled=not fresh or not destination):
            try:
                target = Path(destination).expanduser().resolve()
                if target.is_relative_to(Path(__file__).resolve().parent):
                    raise ValueError("Choose a destination outside this repository.")
                if target.exists():
                    raise ValueError(
                        "Destination exists; choose a new filename to preserve existing work."
                    )
                report.export_relative_csv(target)
                st.success("Private CSV written to the selected destination.")
            except (ValueError, OSError) as exc:
                st.error(str(exc))
