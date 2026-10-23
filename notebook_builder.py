"""Generate a runnable, executed Q1–Q20 notebook with Q20 output cleared."""

import contextlib
import io
import json
from dataclasses import asdict


def build_notebook(report, source_label="synthetic demo"):
    """Execute presentation cells against the completed report, without rereading.

    On an ordinary notebook run, Q1 recomputes the pipeline from SOURCE_PATH or the
    demo. During export only, an injected report preserves the user's completed run.
    No absolute source path or private relative criteria are embedded in the file.
    """
    config = asdict(report.config)
    config.update(relative_last_name="", relative_city="")
    synthetic = source_label.lower() == "synthetic demo"
    introduction = (
        "# Bank Automata Workbench\n\n"
        "Theory of Languages and Machines · fictional bank coursework.\n\n"
        f"Saved output source: **{source_label}**. "
        "Run this notebook from the repository directory with its Python environment. "
        "Q1 recomputes all questions in two bounded passes; later cells explain and display each result. "
        "Set SOURCE_PATH to your local CSV before rerunning on your own data. "
        "The default rerun uses synthetic data. Saved outputs from another dataset will therefore change.\n\n"
        "Q20 is intentionally cleared. Enter personal criteria locally, then export to a new private path. "
        "Understand the implementation in bank_core.py and automata.py for the oral presentation. "
        "Ages use the Shamsi reference year, without birthday adjustment."
    )
    cells = [
        dict(cell_type="markdown", metadata={}, source=introduction.splitlines(True))
    ]
    namespace = {"_prepared_report": report}
    for number in range(1, 21):
        question = report.questions[number]
        explanation = f"## Q{number:02d} · {question['title']}\n\n"
        if number == 2:
            explanation += "The assignment explicitly fills the province field with the birth province’s capital **city**; this unusual rule is preserved.\n"
        elif number in (13, 14, 15, 16, 18):
            explanation += "The explicit state-machine implementations and trace functions are in automata.py. NFAs consume record-evidence tokens. The balance machine is an educational tape/register simulation.\n"
        elif number == 17:
            explanation += "Find the global donor in pass one; zero the donor before distributing integer shares in pass two. Allocate remaining IRR in source order, preserving the total even when the donor is a recipient.\n"
        elif number == 20:
            explanation += "No output is saved or displayed. Relative rows require a separate explicit private CSV export.\n"
        else:
            explanation += "Normalization precedes filtering. Examples are bounded; counts cover the complete source.\n"
        cells.append(
            dict(cell_type="markdown", metadata={}, source=explanation.splitlines(True))
        )
        code = ""
        if number == 1:
            code = (
                "# Configure the source, then execute the bounded pipeline.\n"
                "import json\nfrom pathlib import Path\n"
                "from bank_core import Config, execute_pipeline\nfrom demo import demo_csv\n"
                "SOURCE_PATH = ''  # Empty uses the fictional demo; set a local CSV path here.\n"
                f"config = Config(**{config!r})\n"
                "# During export, the completed report is injected; a normal rerun reads the source.\n"
                'report = globals().pop("_prepared_report", None)\n'
                "if report is None:\n"
                "    report = execute_pipeline(Path(SOURCE_PATH) if SOURCE_PATH else demo_csv(), config=config)\n"
            )
        if number == 20:
            code += (
                "# Set relative_last_name and (without a suffix) relative_city in Config above.\n"
                "# Rerun Q1, then explicitly export outside the repository to a NEW path.\n"
                '# report.export_relative_csv(Path.home() / "private_relatives.csv")\n'
                "# Keep this cell output empty before submission.\n"
            )
        else:
            code += (
                f"# Display Q{number} aggregate results from the completed pipeline.\n"
                f"result = dict(report.questions[{number}])\n"
                + (
                    ""
                    if synthetic
                    else 'result.pop("preview", None)  # Private-source rows stay out of this export.\n'
                )
                + "print(json.dumps(result, ensure_ascii=False, indent=2))\n"
            )
        if number == 9:
            code += """# Draw the two average ages as an inline SVG chart (no plotting dependency).
cohorts = report.questions[9]['summary']
bars = []
for index, (cohort, values) in enumerate(cohorts.items()):
    age = values['average_age']
    width = max(0, age or 0) * 3
    y = 40 + index * 70
    label = 'No records' if age is None else f'{age:.1f} years; n={values["count"]}'
    bars.append(f'<text x="8" y="{y}">{cohort}s</text><rect x="85" y="{y-17}" width="{width}" height="25" fill="#26806b"/><text x="85" y="{y+28}">{label}</text>')
chart = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 180" role="img" aria-label="Average age by birth cohort"><rect width="900" height="180" fill="white"/><g fill="#162b3b" font-family="sans-serif">' + ''.join(bars) + '</g></svg>'
if '_capture_svg' in globals():
    _capture_svg(chart)  # Export captures the same chart as a notebook output.
else:
    from IPython.display import SVG, display
    display(SVG(chart))
"""
        captured = io.StringIO()
        rich_outputs = []
        namespace["_capture_svg"] = lambda svg: rich_outputs.append(
            dict(output_type="display_data", metadata={}, data={"image/svg+xml": svg})
        )
        with contextlib.redirect_stdout(captured):
            exec(compile(code, f"<Q{number}>", "exec"), namespace)
        output = captured.getvalue()
        cells.append(
            dict(
                cell_type="code",
                metadata={},
                execution_count=number,
                source=code.splitlines(True),
                outputs=[]
                if number == 20 or not output
                else [
                    dict(
                        output_type="stream",
                        name="stdout",
                        text=output.splitlines(True),
                    )
                ]
                + rich_outputs,
            )
        )
    document = dict(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.13.5"},
        },
        nbformat=4,
        nbformat_minor=5,
    )
    # Stable IDs avoid notebook-format warnings and noisy diffs on regeneration.
    for index, cell in enumerate(cells):
        cell["id"] = f"bank-cell-{index:02d}"
    return json.dumps(document, ensure_ascii=False, indent=1).encode("utf-8")
